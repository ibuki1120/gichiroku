# テキストファイルを読み込む関数
def read_interaction_as_list(file_path, user):
    """
    指定されたテキストファイルを読み込み、改行ごとにリスト化する
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content_list = [line.strip().replace("UserName", user) for line in file.readlines() if line.strip()]
    return content_list
    

# プロンプトを読み込む
def read_prompt_as_list(file_path, user):
    """
    指定されたテキストファイルを読み込み、改行ごとにリスト化する
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().strip().replace("UserName", user)
    return content