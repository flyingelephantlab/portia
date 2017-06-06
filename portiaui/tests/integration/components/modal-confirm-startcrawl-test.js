import { moduleForComponent, test } from 'ember-qunit';
import hbs from 'htmlbars-inline-precompile';

moduleForComponent('modal-confirm-startcrawl', 'Integration | Component | modal confirm startcrawl', {
  integration: true
});

test('it renders', function(assert) {

  // Set any properties with this.set('myProperty', 'value');
  // Handle any actions with this.on('myAction', function(val) { ... });

  this.render(hbs`{{modal-confirm-startcrawl}}`);

  assert.equal(this.$().text().trim(), '');

  // Template block usage:
  this.render(hbs`
    {{#modal-confirm-startcrawl}}
      template block text
    {{/modal-confirm-startcrawl}}
  `);

  assert.equal(this.$().text().trim(), 'template block text');
});
