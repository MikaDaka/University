// Простейшая функция
function hello() {
    console.log("Hello, world!");
}
hello();

// Функция с параметрами
function sum(a, b) {
    console.log("Сумма:", a + b);
}
sum(5, 7);

// Условные операторы
function checkAge(age) {
    if (age >= 18) {
        console.log("Совершеннолетний");
    } else {
        console.log("Несовершеннолетний");
    }
}
checkAge(16);

// Массивы
let numbers = [1, 2, 3, 4, 5];
console.log("Массив:", numbers);

// Циклы
for (let i = 0; i < numbers.length; i++) {
    console.log("Элемент массива:", numbers[i]);
}
