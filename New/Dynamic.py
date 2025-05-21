{
  "write_data": {
    "0xF193": "a8123",
    "0xF191": "a8123",
    "0xF195": "a8123",
    "0xF1A1": "a812",
    "0xF197": "a812",
    "0xF18B": "a812",
    "0xF18C": "a8112345a8112345a8112345a8112345",
    "0xF1C1": "a8112345a8112345a8112345a8112345",
    "0xF187": "a8123a8123"
  }
}
###
# In your init or setup method

self.info_dids = self.uds_config.get("ecu_information_dids", {})
self.decode_dids = self.uds_config.get("decoding_dids", {})
self.write_data_dict = self.uds_config.get("write_data", {})

# Convert hex strings to int keys
self.client_config["data_identifiers"] = {
    int(did_str, 16): SafeAsciiCodec(length)
    for did_str, length in self.decode_dids.items()
}
self.client_config["write_data"] = {
    int(did_str, 16): data_str
    for did_str, data_str in self.write_data_dict.items()
}



write_data_dict = self.client_config.get('write_data', {})

for tc_id, steps in grouped_cases.items():
    logging.info(f"Running Test Case: {tc_id}")
    for step in steps:
        _, step_desc, service, subfunc, expected = step
        service_int = int(service, 16)
        subfunc_int = int(subfunc, 16)

        try:
            response = None

            if service_int == 0x10:
                response = client.change_session(subfunc_int)
            elif service_int == 0x11:
                response = client.ecu_reset(subfunc_int)
            elif service_int == 0x22:
                response = client.read_data_by_identifier(subfunc_int)
            elif service_int == 0x2E:  # WriteDataByIdentifier
                data_to_write = write_data_dict.get(subfunc_int)
                if data_to_write is None:
                    raise ValueError(f"No write data configured for DID {hex(subfunc_int)}")
                response = client.write_data_by_identifier(subfunc_int, data_to_write)

            elif service_int == 0x19:
                response = client.read_dtc_information(subfunc_int, status_mask=0xFF)
            elif service_int == 0x14:
                response = client.clear_dtc(subfunc_int)
            elif service_int == 0x3E:
                response = client.tester_present()
            elif service_int == 0x85:
                response = client.control_dtc_setting(subfunc_int)

            # Your 0x27 seed/key logic here (unchanged)

            elif service_int == 0x28:
                control_type = subfunc_int
                communication_type = control_type if control_type in [0,1,2,3] else 0
                response = client.communication_control(control_type, communication_type)
            else:
                raise ValueError(f"Unsupported service: {service}")

            # Process response, logging, timing etc...

        except Exception as e:
            logging.error(f"Test case {tc_id} step '{step_desc}' failed: {e}")
            # handle failure or break if needed


####
elif service_int == 0x27:
    if subfunc_int % 2 == 1:  # Request Seed (0x01, 0x11, etc.)
        response = client.request_seed(subfunc_int)
        if not response.positive:
            failure_reason = f"NRC (seed): {hex(response.code)}"
            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
            raise Exception(failure_reason)

        seed = response.service_data.seed
        context[f"seed_{subfunc_int}"] = seed
        logging.info(f"Received Seed (subfunc {hex(subfunc_int)}): {seed.hex()}")
        time.sleep(0.5)

        # Send seed to PC and get key
        udp_ip = "192.168.10.220"
        udp_port = 5005
        max_retries = 3
        retry_delay = 1.0
        expected_key_length = 8  # Modify based on actual level if needed

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

                    context[f"key_{subfunc_int + 1}"] = key  # Store key using subfunc 0x02/0x12
                    logging.info(f"Received Key (for subfunc {hex(subfunc_int + 1)}): {key}")
                    break
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

    elif subfunc_int % 2 == 0:  # Send Key (0x02, 0x12, etc.)
        key = context.get(f"key_{subfunc_int}")
        if not key:
            raise Exception(f"No key available for subfunction {hex(subfunc_int)}. Ensure seed request precedes key send.")

        response = client.send_key(subfunc_int, key)
        if not response.positive:
            failure_reason = f"NRC (key): {hex(response.code)}"
            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
            raise Exception(failure_reason)
    else:
        raise ValueError(f"Unsupported subfunction for service 0x27: {hex(subfunc_int)}")



#####
 with Client(self.conn, request_timeout=2, config=self.client_config) as client:
            context = {}
            print(dir(client))
            print("Effective UDS Client Config:")
            for key,val in self.client_config.items():
                    print(f":{key}:{val}")
            for tc_id, steps in grouped_cases.items():
                logging.info(f"Running Test Case: {tc_id}")
                for step in steps:
                    _, step_desc, service, subfunc, expected = step
                    try:
                        service_int = int(service, 16)
                        subfunc_int = int(subfunc, 16)
                        expected_bytes = [int(b, 16) for b in expected.strip().split()]
                        logging.info(f"{tc_id} - {step_desc}: SID={service}, Sub={subfunc}, Expected={expected_bytes}")

                        request_time = datetime.now()

                        response = None
                        if service_int == 0x10:
                            response = client.change_session(subfunc_int)
                        elif service_int == 0x11:
                            response = client.ecu_reset(subfunc_int)
                        elif service_int == 0x22:
                            response = client.read_data_by_identifier(subfunc_int)
                        elif service_int == 0x2E:  # WriteDataByIdentifier
                            if (subfunc_int == 0xF193)or(subfunc_int == 0xF191)or(subfunc_int == 0xF195):
                               response = client.write_data_by_identifier(subfunc_int,"a8123")
                            if (subfunc_int == 0xF1A1)or(subfunc_int == 0xF197)or(subfunc_int ==0xF18B):
                               response = client.write_data_by_identifier(subfunc_int,"a812")
                            if (subfunc_int == 0xF18C)or(subfunc_int == 0xF1C1):
                               response = client.write_data_by_identifier(subfunc_int,"a8112345a8112345a8112345a8112345")
                            if (subfunc_int == 0xF187):
                               response = client.write_data_by_identifier(subfunc_int,"a8123a8123")
                               
                        elif service_int == 0x19:  # ReadDTCInformation
                            response = client.read_dtc_information(subfunc_int,status_mask=0xFF)
                            
                        elif service_int == 0x14:  # ClearDiagnosticInformation
                            group_of_dtc = subfunc_int
                            response = client.clear_dtc(group_of_dtc)
                            
                        elif service_int == 0x3E:  # TesterPresent
                            response = client.tester_present()
                            
                        elif service_int == 0x85:
                            response = client.control_dtc_setting(subfunc_int)
                        
                       elif service_int == 0x27:
    if subfunc_int % 2 == 1:  # Request Seed (odd subfunction: 0x01, 0x11, etc.)
        response = client.request_seed(subfunc_int)
        if not response.positive:
            failure_reason = f"NRC (seed): {hex(response.code)}"
            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
            raise Exception(failure_reason)
        
        seed = response.service_data.seed
        context[f"seed_{subfunc_int}"] = seed
        logging.info(f"Received Seed (subfunc {hex(subfunc_int)}): {seed.hex()}")
        time.sleep(0.5)

        # Send seed to PC and get key
        udp_ip = "192.168.10.220"
        udp_port = 5005
        max_retries = 3
        retry_delay = 1.0
        expected_key_length = 8  # Modify per security level if needed

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
                    
                    context[f"key_{subfunc_int+1}"] = key  # store key using subfunc 0x02/0x12
                    logging.info(f"Received Key (for subfunc {hex(subfunc_int+1)}): {key}")
                    break
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

    elif subfunc_int % 2 == 0:  # Send Key (even subfunction: 0x02, 0x12, etc.)
        key = context.get(f"key_{subfunc_int}")
        if not key:
            raise Exception(f"No key available for subfunction {hex(subfunc_int)}. Ensure seed request precedes key send.")
        
        response = client.send_key(subfunc_int, key)
        if not response.positive:
            failure_reason = f"NRC (key): {hex(response.code)}"
            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
            raise Exception(failure_reason)
    else:
        raise ValueError(f"Unsupported subfunction for service 0x27: {hex(subfunc_int)}")


                              
                        elif service_int == 0x28:  # CommunicationControl
                             control_type = subfunc_int  # Subfunction
                             #communication_type = 0x00  # Default: Enable Rx and Tx
                             if control_type == 0x00:
                                 communication_type = 0x00  # Enable Rx and Tx
                             elif control_type == 0x01:
                                 communication_type = 0x01  # Enable Rx, disable Tx
                             elif control_type == 0x02:
                                 communication_type = 0x02  # Disable Rx, enable Tx
                             elif control_type == 0x03:
                                 communication_type = 0x03  # Disable Rx and Tx
                             else:
                                 logging.warning(f"Unknown subfunc for CommControl: {hex(control_type)}. Using 0x00.")
                                 communication_type = 0x00
                             response = client.communication_control(control_type, communication_type)
      
                              
                        else:
                            raise ValueError(f"Unsupported service: {service}")                           

                        response_time = datetime.now()
                        
