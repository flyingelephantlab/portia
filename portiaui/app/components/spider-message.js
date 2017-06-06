import Ember from 'ember';
const { computed } = Ember;

export default Ember.Component.extend({
    api: Ember.inject.service(),
    notificationManager: Ember.inject.service(),
    hasSpider: computed.bool('currentSpider'),

    actions: {
        trainSpider(spider) {
            this.get('api').post('train', {
                model: spider,
                jsonData: {data: {type: 'spiders', id: spider.id}}
            }).then(() => {
                this.get('notificationManager').showNotification(
                    'Your spider has been trained successfully');
            }, data => {
                let error = data.errors[0];
                if (error.status > 499) {
                    throw data;
                }
                this.get('notificationManager').showNotification(error.title, error.detail);
            });
        },
        startcrawlSpider(spider) {
            this.get('api').post('start_crawl', {
                model: spider,
                jsonData: {data: {type: 'spiders', id: spider.id}}
            }).then(() => {
                this.get('notificationManager').showNotification(
                    'Your spider is crawling successfully');
            }, data => {
                let error = data.errors[0];
                if (error.status > 499) {
                    throw data;
                }
                this.get('notificationManager').showNotification(error.title, error.detail);
            });
        }
    }

});
