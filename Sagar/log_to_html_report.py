import os
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
# === CONFIGURATION ===
INPUT_ASC_FILE = "/home/mobase/UDS_Tool_Raspberry_Pi/MKBD/udsoncan/output/can_logs/CANLog_Testcase_20250521_121028.asc"
OUTPUT_HTML_FILE = "/home/mobase/UDS_Tool_Raspberry_Pi/MKBD/udsoncan/output/can_logs/CANLog_Report.html"
ALLOWED_IDS = {"716", "71E"}  # Uppercase only (no '0x')


def is_header_or_comment(line):
    return (
        line.strip() == "" or
        line.lower().startswith("base hex") or
        line.lower().startswith("internal") or
        "start of measurement" in line.lower() or
        "begin triggerblock" in line.lower()
    )


def parse_line(line):
    parts = line.strip().split()
    if len(parts) < 7:
        return None
    try:
        timestamp = float(parts[0])
        channel = f"CH{parts[1]}"
        msg_id = parts[2].upper()
        direction = parts[3]
        dtype = parts[4]
        dlc = int(parts[5])
        data = ' '.join(part.upper() for part in parts[6:6 + dlc])
        if msg_id not in ALLOWED_IDS:
            return None
        return {
            "timestamp": timestamp,
            "channel": channel,
            "id": msg_id,
            "direction": direction,
            "dtype": dtype,
            "data": data
        }
    except (ValueError, IndexError):
        return None


def convert_to_styled_html(messages, generated_time, duration):
    grouped = defaultdict(list)
    rx_count = tx_count = 0

    for msg in messages:
        grouped[msg['id']].append(msg)
        if msg["direction"].lower() == "rx":
            rx_count += 1
        else:
            tx_count += 1

    body = ""
    for msg_id, entries in grouped.items():
        body += f'<button class="accordion">▶ CAN ID: {msg_id} - Messages: {len(entries)}</button>\n'
        body += '<div class="panel"><table><tr><th>Timestamp</th><th>Channel</th><th>Direction</th><th>Type</th><th>Data</th></tr>\n'
        for msg in entries:
            row_class = "step-pass" if msg["direction"].lower() == "rx" else "step-fail"
            body += f'<tr class="{row_class}">'
            body += f'<td>{msg["timestamp"]:.6f}</td><td>{msg["channel"]}</td><td>{msg["direction"]}</td>'
            body += f'<td>{msg["dtype"]}</td><td>{msg["data"]}</td></tr>\n'
        body += '</table></div>\n'

    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>CAN Log Styled Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            text-align: center;
        }}
        button.accordion {{
            background-color: #ddd;
            color: black;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            border-radius: 5px;
            margin-bottom: 5px;
        }}
        .pass {{
            color: green;
            font-weight: bold;
        }}
        .fail {{
            color: red;
            font-weight: bold;
        }}
        .panel {{
            display: none;
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
            vertical-align: top;
            overflow-wrap: break-word;
            white-space: normal;
            max-width: 200px;
        }}
        th {{
            background-color: #eee;
        }}
        .step-pass {{
            background-color: #e0f7fa;
        }}
        .step-fail {{
            background-color: #fce4ec;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            const acc = document.getElementsByClassName("accordion");
            for (let i = 0; i < acc.length; i++) {{
                acc[i].addEventListener("click", function () {{
                    this.classList.toggle("active");
                    const panel = this.nextElementSibling;
                    panel.style.display = (panel.style.display === "block") ? "none" : "block";
                }});
            }}

            const ctx = document.getElementById("summaryChart").getContext("2d");
            new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: ['Rx', 'Tx'],
                    datasets: [{{
                        label: 'Message Direction',
                        data: [{rx_count}, {tx_count}],
                        backgroundColor: ['#4CAF50', '#F44336'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }});
    </script>
</head>
<body>
    <h1>CAN Log Styled Report</h1>
    <div style="text-align:center; margin-bottom: 20px;">
        <p><strong>Generated:</strong> {generated_time}</p>
        <p><strong>Total Messages:</strong> {len(messages)}</p>
        <p style="color:green;"><strong>Rx:</strong> {rx_count}</p>
        <p style="color:red;"><strong>Tx:</strong> {tx_count}</p>
        <p><strong>Log Duration:</strong> {duration:.3f} seconds</p>
        <p><strong>Filtered CAN IDs:</strong> {', '.join(ALLOWED_IDS)}</p>
    </div>
    <canvas id="summaryChart" width="300" height="300" style="display: block; margin: 0 auto 30px;"></canvas>
    {body}
</body>
</html>"""

    return html_template


def main(input_path, output_path):
    messages = []
    with open(input_path, 'r') as f:
        for line in f:
            if is_header_or_comment(line):
                continue
            msg = parse_line(line)
            if msg:
                messages.append(msg)

    if not messages:
        print("⚠ No messages found for specified CAN IDs.")
        return

    start_time = messages[0]['timestamp']
    end_time = messages[-1]['timestamp']
    duration = end_time - start_time
    generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = convert_to_styled_html(messages, generated_time, duration)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_path}")


if __name__ == "__main__":
    if not os.path.isfile(INPUT_ASC_FILE):
        print(f"❌ File not found: {INPUT_ASC_FILE}")
    else:
        main(INPUT_ASC_FILE, OUTPUT_HTML_FILE)
