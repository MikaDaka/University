let text = document.getElementById("text");
let btn = document.getElementById("btn");

btn.addEventListener("click", function() {
    text.innerHTML = "Текст был изменён с помощью JavaScript!";
    text.style.color = "red";
});
