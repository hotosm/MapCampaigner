var types_value = {};
var typesOptions = '';

function rerenderFunction() {
    // Also render insights function
    var function_form_content = $('#insight-function .function-form').html().trim();
    if (function_form_content.length > 0) {
        return;
    }
    types_value = JSON.parse($("#types").val());
    function_index = 1;
    $('#insight-function .function-form').html('');
    var index = 0;
    var insightsRendered = [];
    $.each(types_value, function (key, value) {
        var type = value['type'];
        var survey = types[type];
        var feature = survey['feature'];
        var tags = survey['tags'];
        if (tags[feature]) {
            feature += '=' + tags[feature]
        }
        var attibutes_on_insights = value['tags'];
        var attributes = {};
        $.each(attibutes_on_insights, function (index, tag) {
            tag = tag.split('[')[0].trim();
            if (tags[tag]) {
                attributes[tag] = tags[tag];
            } else {
                attributes[tag] = [];
            }
        });

        var default_insights = types[type]['insights'];
        $.each(default_insights, function (insight_index, insight) {
            if ($.inArray(oneTimeFunctions, insightsRendered) === -1) {
                insightsRendered.push(insight);
                $('#insight-function-add').click();
                var row = $('#insight-function .function-form').find('.function-form-row')[index];
                $(row).find('.function-selection').val(insight);
                $(row).find('.function-selection').trigger('change');
                $(row).find('.function-feature').val(feature);
                $(row).find('.function-attributes').val(JSON.stringify(attributes));

                // select type
                $(row).find('.function-type').val(type);
                index += 1;
            }
        });
    });
}
function getTypesSelectionValue() {
    // GET SELECTED TYPES
    var types_value = {};
    $.each(getSelectedTypes(), function (index, addedType) {
        if (addedType) {
            var $wrapper = $('#typesTagsContainer').children().eq(index);
            var $tags = $wrapper.find('.row-tags-wrapper').find('.key-tags');
            var tags = [];
            $.each($tags, function (index, value) {
                var tag = $(value).text();
                tags.push($.trim(tag));
            });

            types_value['type-' + (index + 1)] = {
                type: addedType,
                feature: types[addedType]['feature'],
                tags: tags
            }
        }
    });
    return types_value
}

function getSelectedTypes() {
    var uniqueNames = [];
    $('select[name=types_options]').each(function (index, element) {
        var selectedType = $(element).val();
        if ($.inArray(selectedType, uniqueNames) === -1) {
            uniqueNames.push(selectedType);
        }
    });
    return uniqueNames
}
function addMultipleTypes(typeList) {
    $.each(typeList, function (index, type) {
        var selected_type = type['type'];
        addTypes(selected_type);
    });
}

function addTypes(value) {
    var row = $("<div/>");
    row.addClass("row");

    var column = $("<div/>");
    column.addClass("col-lg-4");
    column.addClass("form-group");
    column.addClass("type-selection");
    row.append(column);

    var select = $("<select />");
    select.addClass('select-types');
    select.attr('id', 'types_options');
    select.attr('name', 'types_options');
    select.html(typesOptions);

    column.append(select);
    select.change(onTypesChange);

    if (value) {
        // Add empty value with no default selection
        if (select.find('option[value="' + value + '"]').length === 0) {
            column.append('' +
                '<div class="edit-custom-type">' +
                '<i class="fa fa-pencil-square-o" aria-hidden="true" data-toggle="modal" data-target="#custom-types-tags"></i>' +
                '</div>');
            select.prepend('<option value="' + value + '">' + value + '</option>');
            select.prop("disabled", true);
        }
        select.prepend('<option value="">Select type</option>');
        select.children().removeAttr('selected');
        select.find('option[value="' + value + '"]').prop('selected', true);
        select.trigger('change');
    } else {
        // Add empty value with default selection
        select.prepend('<option value="" selected="selected">Select type</option>');
    }

    $("#typesTagsContainer").append(row);
}

function onTypesChange() {
    $('.types-required-message').hide();

    var selected_type = this.value;

    var row = $(this).parent().parent();

    var row_tags = row.children('.row-tags');

    if (row_tags) {
        row_tags.remove();
    }

    var column = $("<div/>");
    column.addClass("row-tags");
    column.addClass("col-lg-6");

    row.append(column);

    var div = $("<div />");
    div.addClass("row-tags-wrapper");

    var selected_tags;
    if (typeof selected_types_data !== 'undefined') {
        $.each(selected_types_data, function (index, type) {
            if (type['type'] == selected_type) {
                selected_tags = type['tags'];
            }
            if (!types[type['type']]) {
                addCustomType(type);
                type['tags'] = undefined;
            }
        });
    }

    if (typeof types !== 'undefined') {
        if (types[selected_type]) {
            var key_tags;
            var tags = types[selected_type]['tags'];
            var key_tags_default = Object.keys(tags);

            if (typeof selected_tags != 'undefined') {
                key_tags = Object.keys(selected_tags);
            } else {
                key_tags = Object.keys(tags);
            }
            for (var j = 0; j < key_tags.length; j++) {
                var tag_string = key_tags[j];
                if (tags[tag_string] && tags[tag_string].length > 0) {
                    tag_string += '<span>: ' + tags[tag_string].join(', ') + '</span>';
                }
                div.append(
                    '<span class="key-tags" style="display: inline-block">' + '<i class="fa fa-times remove-tags" onclick="removeIndividualTag(this, \'' + tag_string + '\')" aria-hidden="true"></i>' + tag_string + ' </span>');
            }

            var select_tag = $("<span />");
            select_tag.addClass('select-tag');
            var span_select = $("<ul />");
            span_select.addClass('additional-key-tags');
            for (var j = 0; j < key_tags_default.length; j++) {
                var tag_string = key_tags_default[j];
                if (tags[tag_string] && tags[tag_string].length > 0) {
                    tag_string += '<span>: ' + tags[tag_string].join(', ') + '</span>';
                }
                span_select.append('<li onclick="addTag(this)">' + tag_string + '</li>')
            }
            select_tag.html(span_select);

            div.append('<div class="btn btn-add-tag" type="button" style="margin-left: 5px;" onclick="onAddTags(this)" onblur="onAddTagsFInish(this)">' +
                '<i class="fa fa-plus" style="font-size: 8pt"></i> Add' + select_tag.html() +
                '</div>' +
                '</span>');
            column.html(div);

            // append to parent
            row.prepend('<div class="row-tags">' +
                '<button class="btn btn-remove-type btn-sm"' +
                'type=button onclick="removeTags(this, \'' + selected_type + '\')">' +
                '<i class="fa fa-minus"></i></button></div>');
        }
    }
    $('#insight-function .function-form').html('');
}

function onAddTags(element) {
    if (!$(element).find('.additional-key-tags').is(":visible")) {
        onAddTagsFInish();
        $(element).find('.additional-key-tags').show();
    } else {
        $('.additional-key-tags').hide();
    }
}
function onAddTagsFInish(element) {
    $('.additional-key-tags').hide();
}
function addTag(wrapper) {
    $('#warning-tag').html('');
    $('#insight-function .function-form').html('');
    var $tagWrapper = $(wrapper).closest('.row-tags-wrapper');
    var tag = $(wrapper).text();
    var spans = $tagWrapper.find("span:contains('" + $(wrapper).text() + "')");
    if (spans.length == 0) {
        $tagWrapper.find('.btn-add-tag').before('' +
            '<span class="key-tags" style="display: inline-block">' + '<i class="fa fa-times remove-tags" style="color: grey" onclick="removeIndividualTag(this, \'' + $(wrapper).text() + '\')" aria-hidden="true"></i>' + $(wrapper).text() + ' </span>')
    } else {
        $('#warning-tag').html('Tag is already selected, please select another.');
    }
}
function removeTags(event, type) {
    $(event).parent().parent().remove();
    $('#insight-function .function-form').html('');
}

function removeIndividualTag(event, type) {
    $(event).parent().remove();
    $('#insight-function .function-form').html('');
}