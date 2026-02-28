groupmates = [
    {"name": "Василий", "group": "912-2", "age": 19, "marks": [4, 3, 5, 5, 4]},
    {"name": "Анна", "group": "912-1", "age": 18, "marks": [3, 2, 3, 4, 3]},
    {"name": "Георгий", "group": "912-2", "age": 19, "marks": [3, 5, 4, 3, 5]},
    {"name": "Валентина", "group": "912-1", "age": 18, "marks": [5, 5, 5, 4, 5]},
]

def print_students(students):
    print("Имя".ljust(15), "Группа".ljust(8), "Возраст".ljust(8), "Оценки".ljust(20))
    for s in students:
        print(
            s["name"].ljust(15),
            s["group"].ljust(8),
            str(s["age"]).ljust(8),
            str(s["marks"]).ljust(20)
        )
    print()

if __name__ == "__main__":
    print_students(groupmates)
