class Question_id {
    constructor({url}) {
        this.value = url.split('/')[2]
    }

    get url() {
        return 'https://www.leetcode.com/problems/' + this.value
    }
};


class Question {
    constructor({id, name, tags, description}) {
        this.id = id
        this.name = name
        this.tags = tags
        this.description = description
    }
};


const question_ids = $('[role="rowgroup"]').find('[role="row"]').map(function(index, row) {
    return new Question_id({
        url: $(row).find('a').first().attr('href')})});
