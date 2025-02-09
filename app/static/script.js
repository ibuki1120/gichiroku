document.getElementById("uploadButton").addEventListener("click", function () {
    const userNameInput = document.getElementById("user");
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) {
        alert("MP3 ファイルを選択してください。");
        return;
    }
    if (!userNameInput.value) {
        alert("ユーザ名を入力してください");
        return;
    }

    const loading = document.getElementById("loading");
    loading.style.display = "block";

    const formData = new FormData();
    formData.append("user", userNameInput.value);
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
            document.getElementById("userName").innerText = data.user;
            // document.getElementById("summary").innerText = data.summary;
            const html = marked.parse(data.summary);
            document.getElementById("summary").innerHTML = html;
        }
    })
    .catch(error => {
        console.error("アップロードエラー", error);
    })
    .finally(() => {
        loading.style.display = "none";
    });
});
