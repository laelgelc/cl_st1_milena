#!/bin/bash

# Usage:
# Verify Permissions: chmod +x capture_ao3_lists.sh
# Launch the background process: nohup bash capture_ao3_lists.sh > process_output.log 2>&1 &
# Monitor Progress:
#  Check the progress and errors log: tail -f capture_ao3_lists.log

capture_ao3_lists() {
  source "$HOME"/my_env/bin/activate
  if [ -z "$VIRTUAL_ENV" ]; then
      echo "Error: Virtual environment not activated!"
      exit 1
  fi
  #python capture_ao3_lists.py
  python capture_ao3_lists.py --test
  #python capture_ao3_lists.py --test --user eyamrog
}

stop_instance() {
  # Do not forget to:
  # - have 'aws-cli' installed on the EC2 instance
  # - have the IAM role 'S3-Admin-Access' attached to the EC2 instance

  instance_id=$(aws ec2 describe-instances --filters "Name=private-dns-name,Values=$(hostname --fqdn)" --query "Reservations[*].Instances[*].InstanceId" --output text)
  aws ec2 stop-instances --instance-ids "$instance_id"
  echo "Instance $instance_id stopped."
}

capture_ao3_lists
stop_instance
