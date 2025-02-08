document.getElementById("uploadButton").addEventListener("click", function () {
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) {
        alert("MP3 ファイルを選択してください。");
        return;
    }

    const formData = new FormData();
    formData.append("audio", fileInput.files[0]);

    fetch("/analyze_mp3", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("エラー: " + data.error);
        } else {
            document.getElementById("transcript").innerText = data.transcript;
            document.getElementById("summary").innerText = data.summary;
        }
    })
    .catch(error => {
        console.error("アップロードエラー", error);
    });
});
