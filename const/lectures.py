class Lectures:
    callback = 'lectures'
    description = 'Лекции'

    class MiniCourseBusinessNovice:
        callback = 'mini_course_business_novice'
        link = 'Скоро откроются продажи!'
        description = 'Мини курс "Бизнес новичок"'

    class Intro:
        callback = 'lecture_intro'
        link = 'https://youtu.be/jIM7dNYn1Ns'
        description = 'ТОП 10 ошибок при закупке из Китая. БИЗНЕС С КИТАЕМ'

    list_lectures = [MiniCourseBusinessNovice, Intro]
