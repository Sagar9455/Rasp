elif service_int == 0x28:  # CommunicationControl
    control_type = subfunc_int  # Subfunction
    communication_type = 0x00  # Default: Enable Rx and Tx
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
