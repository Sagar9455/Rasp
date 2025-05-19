udp_ip = "192.168.10.220"
udp_port = 5005
max_retries = 3
retry_delay = 1.0  # seconds
expected_key_length = 4  # Change as needed

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

try:
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempt {attempt}: Sending seed to PC...")
            sock.sendto(seed.hex().encode(), (udp_ip, udp_port))
            key, _ = sock.recvfrom(1024)
            key = key.strip()

            if not key:
                raise Exception("Received empty key from PC")
            if len(key) != expected_key_length:
                raise Exception(f"Invalid key length: expected {expected_key_length}, got {len(key)}")

            logging.info(f"Received Key: {key}")
            break  # Success

        except socket.timeout:
            logging.warning(f"Attempt {attempt} - Timeout waiting for key.")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Timeout after {max_retries} retries waiting for key from PC")

        except Exception as e:
            logging.exception(f"Attempt {attempt} - Error occurred:")
            if attempt == max_retries:
                raise
finally:
    sock.close()


####



elif service_int == 0x27:
    if subfunc_int == 0x11:
        response = client.request_seed(subfunc_int)
        
        if not response.positive:
            failure_reason = f"NRC (seed): {hex(response.code)}"
            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
            raise Exception(failure_reason)

        seed = response.service_data.seed
        logging.info(f"Received Seed: {seed.hex()}")

        # Send seed to PC and receive key with retries
        udp_ip = "192.168.10.220"
        udp_port = 5005
        max_retries = 3
        retry_delay = 1.0  # seconds

        key = None
        for attempt in range(1, max_retries + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            try:
                logging.info(f"Attempt {attempt}: Sending seed to PC...")
                sock.sendto(seed.hex().encode(), (udp_ip, udp_port))
                key, _ = sock.recvfrom(1024)
                logging.info(f"Received Key: {key}")
                break  # Exit loop on success
            except socket.timeout:
                logging.warning(f"Attempt {attempt} - Timeout waiting for key.")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    failure_reason = f"Timeout after {max_retries} retries waiting for key from PC"
                    logging.error(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
                    raise Exception(failure_reason)
            except Exception as e:
                logging.error(f"Attempt {attempt} - Socket error: {e}")
                if attempt == max_retries:
                    raise
            finally:
                sock.close()

        # 3. Send Key to ECU
        try:
            key_bytes = bytes.fromhex(key.decode().strip())
            response = client.send_key(subfunc_int + 1, key_bytes)
            if not response.positive:
                failure_reason = f"NRC (key): {hex(response.code)}"
                logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
                raise Exception(failure_reason)
            logging.info(f"Successfully sent key: {key_bytes.hex()}")
        except Exception as e:
            logging.error(f"Failed to send key to ECU: {e}")
            raise
