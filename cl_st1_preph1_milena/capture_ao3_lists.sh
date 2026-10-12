#!/bin/bash
set -euo pipefail

# Usage:
#   chmod +x capture_ao3_lists.sh  # Optional if the script is run preceded by 'bash'
#   nohup bash capture_ao3_lists.sh > process_output.log 2>&1 &
#   tail -f capture_ao3_lists.log  # Python programme logs
#   tail -f process_output.log  # Shell processing logs

# Important:
# - Switch from test (python -u capture_ao3_lists.py --test) to production (python -u capture_ao3_lists.py) mode when ready
# - This bash script is meant to be run on an AWS EC2 instance:
#   - Have 'aws-cli' installed on the EC2 instance
#   - Have the IAM role 'S3-Admin-Access' attached to the EC2 instance as it allows ec2:StopInstances

capture_ao3_lists() {
  local conda_sh
  local conda_env_name="my_env"

  # Typical Miniconda install location; adjust if yours differs.
  conda_sh="$HOME/miniconda3/etc/profile.d/conda.sh"
  if [[ ! -f "$conda_sh" ]]; then
    echo "Error: conda.sh not found at: $conda_sh" >&2
    echo "Set conda_sh to your Miniconda location (e.g., $HOME/miniconda3/...)." >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$conda_sh"

  conda activate "$conda_env_name"

  if [[ "${CONDA_DEFAULT_ENV:-}" != "$conda_env_name" ]]; then
    echo "Error: conda environment '$conda_env_name' not activated!" >&2
    exit 1
  fi

  # -u makes logs stream immediately (useful with nohup)
  #python -u capture_ao3_lists.py
  python -u capture_ao3_lists.py --test

  conda deactivate || true
}

get_imds_token() {
  curl -fsS -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"
}

imds_get_with_token() {
  local token path
  token="$1"
  path="$2"
  curl -fsS -H "X-aws-ec2-metadata-token: $token" \
    "http://169.254.169.254/latest/${path}"
}

stop_instance() {
  # Prerequisites:
  # - Have 'aws-cli' installed on the EC2 instance
  # - Have the IAM role 'S3-Admin-Access' attached to the EC2 instance as it allows ec2:StopInstances
  command -v aws >/dev/null 2>&1 || { echo "Error: aws CLI not found" >&2; return 0; }

  local token instance_id region
  token="$(get_imds_token)" || { echo "Error: failed to get IMDS token; not stopping instance." >&2; return 0; }

  instance_id="$(imds_get_with_token "$token" "meta-data/instance-id")" || return 0
  region="$(imds_get_with_token "$token" "meta-data/placement/region")" || true

  if [[ -z "${region:-}" ]]; then
    region="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
  fi
  if [[ -z "${region:-}" ]]; then
    echo "Error: AWS region could not be determined; not stopping instance." >&2
    return 0
  fi

  aws ec2 stop-instances --region "$region" --instance-ids "$instance_id" >/dev/null || true
  echo "Instance $instance_id stop requested in region $region."
}

main() {
  trap stop_instance EXIT
  capture_ao3_lists
}

main "$@"