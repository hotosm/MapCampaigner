function addingCustomTypeForm(type_selected, element) {
    rowElements[type_selected] = element;
    var type = types[type_selected];
    // init for easy format #}
    $('#custom_type_name').val(type_selected);
    $('#custom_type_feature').val(type['feature']);
    $('#custom_type_element_type').val(type['element_type']);
    $("#custom_type_feature").trigger("keyup");
    $.each(type['tags'], function (key, value) {
        var tag_value = key.replace(': ', '=');
        if (value.length > 0) {
            tag_value += '=' + value.join();
        }
        if (type['feature'] != tag_value) {
            addNewCustomTags(tag_value)
        }
    });
    $('#easy-format #btn-add-custom-type').html('Save');
    $('#yaml-format #btn-add-custom-type').html('Save');

    // init for yaml format #}
    var yamlType = $.extend({}, type);
    delete yamlType['insights'];
    delete yamlType['custom'];
    var tags = [];
    $.each(yamlType['tags'], function (key, value) {
        if (value.length == 0) {
            var keys = key.split(': ');
            if (keys[1]) {
                var thisTag = {};
                var thisTagKeys = keys[1].split(',');
                $.each(thisTagKeys, function (index, value) {
                    thisTagKeys[index] = $.trim(value);
                });
                thisTag[keys[0]] = thisTagKeys;
                tags.push(thisTag);
            } else {
                tags.push(key);
            }
        } else {
            var thisTag = {};
            thisTag[key] = value;
            tags.push(thisTag);
        }
    });
    yamlType['tags'] = tags;
    var cleanYamlType = {};
    cleanYamlType[type_selected] = yamlType;
    $('#yaml-input').val(
        $('#yaml-input').val() + jsyaml.dump(cleanYamlType)
    );

    $('#modal-home').removeClass('active');
    $('#modal-yaml').removeClass('active');
    $('#modal-template').removeClass('active');

    $('#li-template').removeClass('active').addClass('disabled');
    $('#li-home').removeClass('active').addClass('disabled');
    $('#li-yaml').removeClass('active');

    $('#li-template a').removeAttr('data-toggle');
    $('#li-home a').removeAttr('data-toggle');

    $('#li-custom').addClass('active');
    $('#modal-custom').addClass('active').addClass('in');
}

function switchToYamlFormat() {
    $('#yaml-format').show();
    $('#easy-format').hide();
}

function switchToEasyFormat() {
    $('#yaml-format').hide();
    $('#easy-format').show();
}

function addCustomType(typeData) {
    types[typeData['type']] = {
        feature: typeData['feature'],
        insights: [
            "FeatureAttributeCompleteness",
            "CountFeature",
            "MapperEngagement"
        ],
        tags: typeData['tags'],
        element_type: typeData['element_type'],
        custom: true
    };
}

function modalReset() {
    rowElements = {};
    $('#custom-types-tags .modal-title').html('+ Add custom type');
    $('#btn-add-custom-type').html('Add');
    $('#custom_type_name').val('');
    $('#custom_type_feature').val('');
    $('#custom_type_element_type').val('');
    $('#custom-tags').html('');
    $('.modal-required-message').hide()
    $('#yaml-input').val($('#yaml-input').html());
    $('#switch-to-easy-format').show();
}

function addNewCustomTags(value, is_required) {
    if (!is_required || $('#required-custom-tag-row').length == 0) {
        var template = _.template($("#_custom_new_tag").html());
        var html = template({
            is_required: is_required
        });
        $('#custom-tags').append(html);
        if (value) {
            $('#custom-tags').children().last().find('input').val(value);
        }
    }
    if (is_required) {
        $('#required-custom-tag-row').find('input').val(value);
    }
}

function removeCustomTags(element) {
    $(element).closest('.custom-tag-row').remove();
}

function showCustomTypeRequiredMessage(element) {
    $(element).closest('.form-group').find('.modal-required-message').show();
}

function customTypeToTypeFormat() {
    var type_json = {
        feature: $('#custom_type_feature').val(),
        insights: [
            "FeatureAttributeCompleteness",
            "CountFeature",
            "MapperEngagement"
        ],
        tags: {},
        element_type: $('#custom_type_element_type').val(),
        custom: true
    };
    $('.custom-tag-input').each(function (i, tag) {
        var vals = $(tag).val().split('=');
        var key = vals[0];
        if (vals[1]) {
            type_json['tags'][key] = vals[1].split(',');
        } else {
            type_json['tags'][key] = [];
        }
    });
    return {
        custom_type_name: $('#custom_type_name').val(),
        custom_type_value: type_json
    };
}

function saveCustomType() {
    $('.modal-required-message').hide();
    // check name #}
    var $name = $('#custom_type_name');
    if (!$name.val()) {
        showCustomTypeRequiredMessage($name);
    }
    // check feature #}
    var $feature = $('#custom_type_feature');
    if (!$feature.val()) {
        showCustomTypeRequiredMessage($feature);
    }
    // check tags #}
    if ($('.custom-tag-input').length === 0) {
        $('#tag-requirement-message').show();
    }
    $('.custom-tag-input').each(function (i, tag) {
        if (!$(tag).val()) {
            showCustomTypeRequiredMessage(tag);
        }
    });
    var $element_type = $('#custom_type_feature');
    // save if there is no error #}
    if ($('.modal-required-message:visible').length === 0) {
        var customType = customTypeToTypeFormat();
        var name = customType['custom_type_name'];
        var value = customType['custom_type_value'];
        if (!rowElements[name] && types[name]) {
            $('.modal-footer .modal-required-message').show();
        } else {
            $(rowElements[name]).remove();
            $('#custom-types-tags').modal('toggle');
            types[name] = value;
            addTypes(name)
        }
    }
}

function displayError(message) {
    $('.modal-error-message').show();
    $('.modal-error-message').html('Error: ' + message);
}

function appendError(field, key) {
    return '<p> No <b>' + field +'</b> element as child of <b>' + key + '</b><p>'
}

function appendRepeated(key) {
    return '<p> Type <b>' + key +'</b> already registered <p>'
}

function ReorderTags(element) {
    let cleanTags = {};
    $.each(element['tags'], function (index, value) {
        if ($.type(value) === 'string') {
            cleanTags[value] = [];
        }
        else {
            let key = Object.keys(value)[0];
            cleanTags[key] = value[key];
        }
    });

    return cleanTags
}

function saveYamlCustomType() {
    $('.modal-required-message,.modal-error-message').hide();

    let data;
    try {
        data = jsyaml.load($('#yaml-input').val());
    } catch(error) {
        displayError(error.message); return
    }
    if (typeof data === 'undefined') {
        displayError('Empty text area'); return
    }
    // Error message.
    let message = '';

    let rowelements_keys = Object.keys(rowElements);
    let data_keys = Object.keys(data);

    // We cannot add types when editing..
    if (rowelements_keys.length === 1 && data_keys.length > 1) {
        displayError("You cannot add types when editing"); return
    }

    // We need to check that types are not repeated.
    if (rowelements_keys.length === 0) {
        let types_keys = Object.keys(types);

        // Find the intersection of both arrays.
        data_keys = data_keys.filter(key => types_keys.includes(key));
        data_keys.forEach(function(key){
            message += appendRepeated(key)
        });
        if (message !== '') {
            displayError(message); return
        }
    }

    let fields = ['feature', 'tags', 'element_type'];
    // TODO: Include geometry checker.
    // Iterate over fields to check.
    $.each(data, function (key, value) {
        fields.map(function(field) {
            if (!value[field]) {
                message += appendError(field, key);
            }
        });
    });
    if (message !== '') {
        displayError(message); return
    }

    // If all fields are ok, iterate over tags.
    $.each(data, function (key, elements) {
        cleanTags = ReorderTags(elements)
        // Include additional fields.
        elements['custom'] = true;
        elements['insights'] = [
            "FeatureAttributeCompleteness",
            "CountFeature",
            "MapperEngagement"
        ];
        elements['tags'] = cleanTags;
    });

    // include items into the DOM.
    $.each(data, function (key, value) {
        if (rowelements_keys.includes(key)) {
            $(rowElements[key]).remove();
        }
        types[key] = value;
        addTypes(key);
    });
    $('#custom-types-tags').modal('toggle');
}
