import Component from 'ember-modal-dialog/components/modal-dialog';

export default Component.extend({
    translucentOverlay: true, // override default of false
    containerClassNames: 'modal-confirm-startcrawl',
    destinationElementId: 'modal-overlays',

    actions: {
        toggleSubclassed: function() {
            this.sendAction('toggleModal');
        }
    }
});
