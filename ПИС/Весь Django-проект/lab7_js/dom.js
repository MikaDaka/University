let text = document.getElementById("text");
let btn = document.getElementById("btn");

btn.addEventListener("click", function() {
    text.innerHTML = "Текст изменён!";
    text.style.color = "red";
});
