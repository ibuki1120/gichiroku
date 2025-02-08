# テキストファイルを読み込む関数
def read_text_file_as_list(file_path):
    """
    指定されたテキストファイルを読み込み、改行ごとにリスト化する
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
        return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None