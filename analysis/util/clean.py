import re


def clean_content(content):
    cleaned = content

    cleaned = cleaned.replace("\n", " ").replace("\t", " ")
    cleaned = re.sub(r" +", " ", cleaned)
    cleaned = re.sub(r"[#*`>_-]", "", cleaned)
    cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cleaned)
    cleaned = re.sub(r"http\S+", "", cleaned)
    cleaned = cleaned.strip()

    cleaned = re.sub(r" +", " ", cleaned).strip()
    patterns_to_remove = [
        r"Assista também.*",
        r"Leia também.*",
        r"Veja também.*",
        r"Compartilhe.*",
        r"Assista.*vídeo.*",
        r"Reproduzir.*",
        r"VÍDEOS:.*",
        r"Mais do G1.*",
        r"Resumo do dia.*",
    ]

    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned
