
def clean_agent_output(output):
    parts = []

    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
    else:
        parts.append(str(output))

    return "\n".join(parts).replace("**", "").strip()