import socket

...

for step in steps:
    _, step_desc, service, subfunc, expected = step
    try:
        service_int = int(service, 16)
        subfunc_int = int(subfunc, 16)
        expected_bytes = [int(b, 16) for b in expected.strip().split()]
        logging.info(f"{tc_id} - {step_desc}: SID={service}, Sub={subfunc}, Expected={expected_bytes}")

        request_time = datetime.now()
        response = None
        status = "Fail"
        failure_reason = "-"

        if service_int == 0x10:
            response = client.change_session(subfunc_int)

        elif service_int == 0x11:
            response = client.ecu_reset(subfunc_int)

        elif service_int == 0x22:
            response = client.read_data_by_identifier(subfunc_int)

        elif service_int == 0x27:
            # 1. Request Seed
            seed_subfunc = subfunc_int
            response = client.security_access(seed_subfunc)

            if not response.positive:
                failure_reason = f"NRC (seed): {hex(response.code)}"
                logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
                raise Exception(failure_reason)

            seed = response.service_data.seed
            logging.info(f"Received Seed: {seed.hex()}")

            # 2. Send seed to PC via UDP
            udp_ip = "192.168.1.100"   # PC IP address
            udp_port = 5005            # Match with PC's UDP server
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)

            try:
                sock.sendto(seed, (udp_ip, udp_port))
                key, _ = sock.recvfrom(1024)
                logging.info(f"Received Key: {key.hex()}")
            except socket.timeout:
                failure_reason = "Timeout waiting for key from PC"
                logging.error(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
                raise Exception(failure_reason)
            finally:
                sock.close()

            # 3. Send Key
            key_subfunc = seed_subfunc + 1
            response = client.security_access(key_subfunc, key)

        else:
            raise ValueError(f"Unsupported service: {service}")

        response_time = datetime.now()

        if first_request_time is None:
            first_request_time = request_time
            last_response_time = response_time

        if response.positive:
            actual = list(response.original_payload)
            if actual[:len(expected_bytes)] == expected_bytes:
                status = "Pass"
                logging.info(f"{tc_id} {step_desc} -> PASS")
            else:
                failure_reason = f"Expected {expected_bytes}, got {actual}"
                logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
        else:
            failure_reason = f"NRC: {hex(response.code)}"
            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")

    except Exception as e:
        response_time = datetime.now()
        status = "Fail"
        failure_reason = str(e)
        logging.error(f"{tc_id} {step_desc} -> EXCEPTION - {failure_reason}")

    oled.display_centered_text(f"{tc_id}\n{step_desc[:20]}\n{status}")
    time.sleep(2)

    relative_request_time = f"{(request_time - start_time).total_seconds():.6f}"
    relative_response_time = f"{(response_time - start_time).total_seconds():.6f}"

    report_entries.append({
        "id": tc_id,
        "timestamp": relative_request_time,
        "response_timestamp": relative_response_time,
        "description": step_desc,
        "type": "Request Sent",
        "status": status,
        "failure_reason": failure_reason
    })
