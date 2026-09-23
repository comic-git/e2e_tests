/* Map widget for comic_git CMS page metadata and transcripts. */
(function () {
  'use strict';

  function rowsFromValue(value) {
    if (value && typeof value.toJS === 'function') {
      value = value.toJS();
    }
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      return [];
    }
    return Object.keys(value).map(function (key) {
      return { key: key, value: value[key] };
    });
  }

  function validationError(rows) {
    var keys = Object.create(null);
    for (var index = 0; index < rows.length; index += 1) {
      var key = rows[index].key.trim();
      if (!key) {
        return 'Metadata names cannot be blank.';
      }
      if (Object.prototype.hasOwnProperty.call(keys, key)) {
        return 'Each metadata name can appear only once.';
      }
      keys[key] = true;
    }
    return '';
  }

  function valueFromRows(rows) {
    return rows.reduce(function (metadata, row) {
      metadata[row.key.trim()] = row.value;
      return metadata;
    }, {});
  }

  function fieldOption(field, name, fallback) {
    if (field && typeof field.get === 'function') {
      return field.get(name, fallback);
    }
    return fallback;
  }

  var SocialMediaMapControl = window.createClass({
    getInitialState: function () {
      return { rows: rowsFromValue(this.props.value) };
    },

    componentWillReceiveProps: function (nextProps) {
      if (nextProps.value !== this.props.value) {
        this.setState({ rows: rowsFromValue(nextProps.value) });
      }
    },

    isValid: function () {
      var error = validationError(this.state.rows);
      return error ? { error: { message: error } } : { error: false };
    },

    updateRows: function (rows) {
      this.setState({ rows: rows });
      if (!validationError(rows)) {
        this.props.onChange(valueFromRows(rows));
      }
    },

    updateRow: function (index, field, event) {
      var rows = this.state.rows.map(function (row, rowIndex) {
        if (rowIndex !== index) {
          return row;
        }
        var updatedRow = { key: row.key, value: row.value };
        updatedRow[field] = event.target.value;
        return updatedRow;
      });
      this.updateRows(rows);
    },

    updateValue: function (index, value) {
      var rows = this.state.rows.map(function (row, rowIndex) {
        return rowIndex === index ? { key: row.key, value: value } : row;
      });
      this.updateRows(rows);
    },

    addRow: function () {
      this.updateRows(this.state.rows.concat([{ key: '', value: '' }]));
    },

    removeRow: function (index) {
      this.updateRows(this.state.rows.filter(function (_row, rowIndex) {
        return rowIndex !== index;
      }));
    },

    focus: function () {
      var firstInput = document.getElementById(this.props.forID + '-key-1');
      if (firstInput) {
        firstInput.focus();
      }
    },

    render: function () {
      var self = this;
      var error = validationError(this.state.rows);
      var disabled = this.props.isDisabled;
      var field = this.props.field;
      var keyLabel = fieldOption(field, 'key_label', 'Social media key');
      var valueLabel = fieldOption(field, 'value_label', 'Social media value');
      var rowLabel = fieldOption(field, 'row_label', 'social media');
      var addLabel = fieldOption(field, 'add_label', 'Add metadata');
      var valueMarkdown = fieldOption(field, 'value_markdown', false);
      var markdownControl = valueMarkdown ? this.props.resolveWidget('markdown').control : null;
      var keyWidth = Math.min(32, Math.max(8, this.state.rows.reduce(function (longest, row) {
        return Math.max(longest, row.key.length + 2);
      }, 0))) + 'ch';
      return window.h(
        'div',
        {
          className: this.props.classNameWrapper + ' cg-map-widget' +
            (valueMarkdown ? ' cg-map-transcripts' : ' cg-map-metadata'),
          style: { '--cg-key-width': keyWidth },
        },
        window.h('div', { className: valueMarkdown ? 'cg-transcript-list' : 'cg-metadata-grid' },
          this.state.rows.map(function (row, index) {
            var number = index + 1;
            var remove = window.h(
              'button',
              {
                type: 'button',
                className: 'cg-map-remove',
                disabled: disabled,
                'aria-label': 'Remove ' + rowLabel + ' row ' + number,
                title: 'Remove ' + rowLabel,
                onClick: self.removeRow.bind(self, index),
              },
              window.h('span', { className: 'cg-map-remove-glyph', 'aria-hidden': true }, '\u00d7'),
            );
            var keyInput = window.h('input', {
              id: self.props.forID + '-key-' + number,
              type: 'text',
              value: row.key,
              disabled: disabled,
              'aria-label': keyLabel + ' ' + number,
              onChange: self.updateRow.bind(self, index, 'key'),
              placeholder: keyLabel,
              className: 'cg-map-input',
            });
            if (valueMarkdown) {
              return window.h('div', { key: number, className: 'cg-transcript-row' },
                window.h('div', { className: 'cg-transcript-header' }, keyInput, remove),
                window.h('div', {
                  className: 'cg-transcript-editor',
                  role: 'group',
                  'aria-label': valueLabel + ' ' + number,
                }, window.h(markdownControl, {
                  onChange: self.updateValue.bind(self, index),
                  onAddAsset: self.props.onAddAsset,
                  getAsset: self.props.getAsset,
                  classNameWrapper: self.props.classNameWrapper,
                  editorControl: self.props.editorControl,
                  value: row.value,
                  field: field.set('widget', 'markdown').set('minimal', true),
                  getEditorComponents: self.props.getEditorComponents,
                  getRemarkPlugins: self.props.getRemarkPlugins,
                  resolveWidget: self.props.resolveWidget,
                  t: self.props.t,
                  isDisabled: disabled,
                })),
              );
            }
            return window.h(
              'div',
              { key: number, className: 'cg-metadata-row' },
              keyInput,
              window.h('input', {
                type: 'text',
                value: row.value,
                disabled: disabled,
                'aria-label': valueLabel + ' ' + number,
                onChange: self.updateRow.bind(self, index, 'value'),
                placeholder: valueLabel,
                className: 'cg-map-input',
              }),
              remove,
            );
          })),
        window.h(
          'button',
          {
            type: 'button',
            disabled: disabled,
            onClick: this.addRow,
          },
          addLabel,
        ),
        error
          ? window.h(
            'p',
            { role: 'alert', className: 'cg-map-error' },
            error,
          )
          : null,
      );
    },
  });

  window.CMS.registerWidget({
    name: 'comic-git-map',
    controlComponent: SocialMediaMapControl,
    allowMapValue: true,
    schema: {
      properties: {
        key_label: { type: 'string' },
        value_label: { type: 'string' },
        row_label: { type: 'string' },
        add_label: { type: 'string' },
        value_markdown: { type: 'boolean' },
      },
    },
  });
}());
