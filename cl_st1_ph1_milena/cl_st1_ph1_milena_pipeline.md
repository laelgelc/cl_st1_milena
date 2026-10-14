# Corpus Linguistics - Study 1 - Phase 1 - Milena

Run the commands from the project phase directory, e.g.:

```text
cl_st1_ph2_milena/
```

## 1. Data Collection

### 1.1. Lists Collection

#### Test run with 10 pages

```shell
python capture_ao3_lists.py --test-limit 10
```

#### EC2 full run with `tmux`

```shell
bash run_python_ec2.sh \
    capture_ao3_lists.py \
    --no-test-mode \
    --browser chrome \
    --request-delay 3 \
    --request-jitter 1
```

### 1.2. Extract Metadata

#### Default extraction

```shell
python extract_ao3_works_metadata.py
```

### 1.3. Collect Works

### Test run with 10 works

```shell
python capture_ao3_works.py --test-limit 10
```

#### EC2 full run with `tmux`

```shell
bash run_python_ec2.sh \
    capture_ao3_works.py \
    --no-test-mode \
    --browser chrome \
    --request-delay 3 \
    --request-jitter 1
```
