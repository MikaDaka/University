function hello() {
    console.log("Hello, world!");
}
hello();

function sum(a, b) {
    console.log("Сумма:", a + b);
}
sum(5, 7);

function checkAge(age) {
    if (age >= 18) {
        console.log("Совершеннолетний");
    } else {
        console.log("Несовершеннолетний");
    }
}
checkAge(16);

let numbers = [1, 2, 3, 4, 5];
for (let n of numbers) {
    console.log("Элемент:", n);
}
