function make_url(path_parts) {
    return _.flatten([path_parts]).join('/');
}

class Question_id {
    constructor({url}) {
        this.value = url.split('/')[2]
    }
};

class Questions_page {
    constructor(number) {
        this.number = number
    }

    get __url() {
        return make_url(['?page=' + String(this.number)]);
    }

    async with_close({f}) {
        let page = window.open(this.__url);
        await new Promise(function(resolve) {
            page.onload = function () {
                console.log('url after loading' + page.location.href);
                console.log($(page.document).find('[role="rowgroup"]').find('[role="row"]').map(function(index, row) {
                    return new Question_id({
                        url: $(row).find('a').first().attr('href')
                    });
                }));
                resolve();
            };
        });
        let result = f(page);
        page.close();
        return result;
    }
}

class Question {
    constructor({id, name, tags, description}) {
        this.id = id
        this.name = name
        this.tags = tags
        this.description = description
    }
};

async function run_after({f, seconds, args}) {
    await new Promise(function (resolve) {
        _.delay(resolve, seconds * 1000)
    });
    return f(args);
}

function question_ids_on_page({questions_page}) {
    return questions_page.with_close({
        f: function(page) {
            return $(page.document).find('[role="rowgroup"]').find('[role="row"]').map(function(index, row) {
                return new Question_id({
                    url: $(row).find('a').first().attr('href')
                });
            });
        }})
}

const seconds_between_requests_to_avoid_getting_rate_limited = 2;

const number_of_questions_pages = parseInt($('.grid').find('[role="navigation"]').find('[aria-label="next"]').prev().text());

const question_ids = await _.range(number_of_questions_pages, number_of_questions_pages + 1).reduce(async function(question_ids_promise, page_number) {
    const question_ids = await question_ids_promise;
    const questions_page = new Questions_page(page_number);
    const question_ids_on_this_page = await run_after({
        f: question_ids_on_page,
        seconds: seconds_between_requests_to_avoid_getting_rate_limited,
        args: {questions_page: questions_page}});
    console.log(question_ids_on_this_page);
    return question_ids.concat(question_ids_on_this_page);
}, []);

console.log(question_ids)
