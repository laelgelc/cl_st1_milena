#!/usr/bin/env bash
set -euo pipefail

# Usage examples:
#   # Simple: run a script with no extra args
#   nohup bash run_python_ec2.sh my_script.py > process_output.log 2>&1 &
#   nohup bash run_python_ec2.sh dummy.py > process_output.log 2>&1 &
#
#   # With script arguments
#   nohup bash run_python_ec2.sh capture_ao3_lists.py --test > process_output.log 2>&1 &
#   nohup bash run_python_ec2.sh dummy.py --test > process_output.log 2>&1 &
#
#   # Tail logs in another shell
#   tail -f process_output.log
#   tail -f dummy.log

# Configuration
CONDA_ENV_NAME="my_env"              # Change to your environment name
CONDA_SH="${HOME}/miniconda3/etc/profile.d/conda.sh"  # Adjust if Miniconda/conda is elsewhere

# --- Python runner ----------------------------------------------------------

run_python_program() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <python_program> [args...]" >&2
    exit 1
  fi

  local python_program="$1"
  shift
  local python_args=("$@")

  if [[ ! -f "$CONDA_SH" ]]; then
    echo "Error: conda.sh not found at: $CONDA_SH" >&2
    echo "Update CONDA_SH in this script to match your Miniconda/conda installation." >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$CONDA_SH"

  conda activate "$CONDA_ENV_NAME"

  if [[ "${CONDA_DEFAULT_ENV:-}" != "$CONDA_ENV_NAME" ]]; then
    echo "Error: conda environment '$CONDA_ENV_NAME' not activated!" >&2
    exit 1
  fi

  # -u for unbuffered output (logs stream immediately, useful with nohup)
  python -u "$python_program" "${python_args[@]}"

  conda deactivate || true
}

# --- EC2 helper functions ---------------------------------------------------

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
  # Prerequisites (when used on EC2):
  # - aws CLI installed
  # - IAM role attached that allows ec2:StopInstances on this instance
  command -v aws >/dev/null 2>&1 || { echo "Warning: aws CLI not found; not stopping instance." >&2; return 0; }

  local token instance_id region
  token="$(get_imds_token)" || { echo "Warning: failed to get IMDS token; not stopping instance." >&2; return 0; }

  instance_id="$(imds_get_with_token "$token" "meta-data/instance-id")" || return 0
  region="$(imds_get_with_token "$token" "meta-data/placement/region")" || true

  if [[ -z "${region:-}" ]]; then
    region="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
  fi
  if [[ -z "${region:-}" ]]; then
    echo "Warning: AWS region could not be determined; not stopping instance." >&2
    return 0
  fi

  aws ec2 stop-instances --region "$region" --instance-ids "$instance_id" >/dev/null || true
  echo "Instance $instance_id stop requested in region $region."
}

# --- Main -------------------------------------------------------------------

main() {
  # Always attempt to stop the instance when this script exits (success or failure).
  # If you only want to stop on success, move stop_instance after run_python_program
  # and remove this trap.
  # For instance:
  #main() {
  #      if run_python_program "$@"; then
  #        stop_instance
  #      fi
  #    }
  trap stop_instance EXIT

  run_python_program "$@"
}

main "$@"