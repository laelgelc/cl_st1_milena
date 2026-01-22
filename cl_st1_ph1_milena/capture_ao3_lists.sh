#!/bin/bash
set -euo pipefail

# Usage:
#   chmod +x capture_ao3_lists.sh
#   nohup bash capture_ao3_lists.sh > process_output.log 2>&1 &
#   tail -f capture_ao3_lists.log  # Python programme logs
#   tail -f process_output.log  # Shell processing logs

# Important: Switch from test (python -u capture_ao3_lists.py --test) to production (python -u capture_ao3_lists.py) mode when ready

capture_ao3_lists() {
  local venv_activate="$HOME/my_env/bin/activate"
  if [[ ! -f "$venv_activate" ]]; then
    echo "Error: Virtualenv activate script not found at: $venv_activate" >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$venv_activate"

  if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "Error: Virtual environment not activated!" >&2
    exit 1
  fi

  # -u makes logs stream immediately (useful with nohup)
  #python -u capture_ao3_lists.py
  python -u capture_ao3_lists.py --test
  #python -u capture_ao3_lists.py --test --user eyamrog
}

get_imds_token() {
  curl -fsS -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"
}

get_instance_id() {
  local token
  token="$(get_imds_token)"
  curl -fsS -H "X-aws-ec2-metadata-token: $token" \
    "http://169.254.169.254/latest/meta-data/instance-id"
}

get_region() {
  local token doc region
  token="$(get_imds_token)"
  doc="$(curl -fsS -H "X-aws-ec2-metadata-token: $token" \
    "http://169.254.169.254/latest/dynamic/instance-identity/document")"
  region="$(python - <<'PY'
import json,sys
print(json.load(sys.stdin)["region"])
PY
<<<"$doc")"
  echo "$region"
}

stop_instance() {
  # Prereqs:
  # - aws CLI installed
  # - instance role allows ec2:StopInstances on itself
  command -v aws >/dev/null 2>&1 || { echo "Error: aws CLI not found" >&2; return 0; }

  local instance_id region
  instance_id="$(get_instance_id)"
  region="$(get_region)"

  aws ec2 stop-instances --region "$region" --instance-ids "$instance_id" >/dev/null || true
  echo "Instance $instance_id stop requested in region $region."
}

main() {
  trap stop_instance EXIT

  capture_ao3_lists
}

main "$@"