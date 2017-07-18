var addedTypes = [];
var typesOptions = '';

function getTypesSelectionValue() {
    // GET SELECTED TYPES
    var types_value = {};
    $.each(addedTypes, function (index, addedType) {
        if (addedType) {
            var $wrapper = $('#typesTagsContainer').children().eq(index);
            var $tags = $wrapper.find('.row-tags-wrapper').find('.key-tags');
            var tags = [];
            var survey = types[addedType];
            var surveyTags = Object.keys(survey['tags']);
            $.each($tags, function (index, value) {
                var tag = $(value).text();
                tags.push($.trim(tag));
            });

            var is_same = true;
            for (var i = 0; i < surveyTags.length; i++) {
                if ($.inArray(surveyTags[i], tags) < 0) {
                    is_same = false;
                    break
                }
            }
            if (is_same) {
                tags = [];
            }
            types_value['type-' + (index + 1)] = {
                type: addedType,
                tags: tags
            }
        }
    });

    // Also render insights function
    $('#quality-function .function-form').html('');
    var index = 0;
    $.each(types_value, function (key, value) {
        var type = value['type'];
        var survey = types[type];
        var feature = survey['feature'];
        var tags = survey['tags'];
        if (tags[feature]) {
            feature += '=' + tags[feature]
        }
        var attibutes_on_insights = 'all';
        if (value['tags'].length !== 0) {
            attibutes_on_insights = value['tags'].join()
        }
        var default_insights = types[type]['insights'];
        $.each(default_insights, function (insight_index, insight) {
            $('#quality-function-add').click();
            var row = $('#quality-function .function-form').find('.function-form-row')[index];
            $(row).find('.function-selection').val(insight);
            $(row).find('.function-selection').trigger('change');
            $(row).find('.function-selection').data('type', type);
            $(row).find('.function-feature').val(feature);
            $(row).find('.function-attributes').val(attibutes_on_insights);
            index += 1;
        });
    });
    return types_value
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
    select.html(typesOptions)

    column.append(select);
    select.change(onTypesChange);

    if (value) {
        // Add empty value with no default selection
        select.prepend('<option value="">Select type</option>');
        select.children().removeAttr('selected');
        select.find('option[value="' + value + '"]').prop('selected', true);
        select.trigger('change');
    } else {
        // Add empty value with default selection
        select.prepend('<option value="" selected="selected">Select type</option>');
    }

    $("#typesTagsContainer").append(row);
    var addedTypesIndex = addedTypes.length;
    addedTypes[addedTypesIndex] = value;
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

    if (typeof types !== 'undefined') {
        if (types[selected_type]) {
            var tags = types[selected_type]['tags'];
            var key_tags = Object.keys(tags);

            for (var j = 0; j < key_tags.length; j++) {
                div.append('<span class="key-tags" style="display: inline-block">' + key_tags[j] + '<i class="fa fa-times remove-tags" onclick="removeIndividualTag(this, \'' + key_tags[j] + '\')" aria-hidden="true"></i>' + ' </span>');
            }

            var select_tag = $("<span />");
            select_tag.addClass('select-tag');
            var span_select = $("<ul />");
            span_select.addClass('additional-key-tags');
            for (var j = 0; j < key_tags.length; j++) {
                span_select.append('<li onclick="addTag(this)">' + key_tags[j] + '</li>')
            }
            select_tag.html(span_select);

            div.append('<div class="btn btn-danger btn-add-tag" type="button" style="margin-left: 5px;" onclick="onAddTags(this)" onblur="onAddTagsFInish(this)">' +
                '<i class="fa fa-plus" style="font-size: 8pt"></i> Add tag' + select_tag.html() +
                '</div>' +
                '</span>');
            column.html(div);

            // append to parent
            row.append('<div class="col-lg-1 row-tags">' +
                '<button class="btn btn-danger btn-sm btn-block"' +
                'type=button onclick="removeTags(this, \'' + selected_type + '\')">' +
                '<i class="fa fa-minus"></i></button></div>');
        }
    }

    var typeIndex = row.index();
    addedTypes[typeIndex] = selected_type;

    // Hide add/remove tags when basic mode.
    var setting = $('#dashboard_settings option:selected').text();
    if (setting.toLowerCase() != 'advanced') {
        $('.remove-tags').hide();
        $('.btn-add-tag').hide();
    }
}

function onAddTags(element) {
    if (!$(element).find('.additional-key-tags').is(":visible")) {
        $(element).find('.additional-key-tags').show();
    } else {
        $('.additional-key-tags').hide();
    }
}
function onAddTagsFInish(element) {
    $('.additional-key-tags').hide();
}
function addTag(wrapper) {
    var $tagWrapper = $(wrapper).closest('.row-tags-wrapper');
    var tag = $(wrapper).text();
    var spans = $tagWrapper.find("span:contains('" + $(wrapper).text() + "')");
    if (spans.length == 0) {
        $tagWrapper.find('.btn-add-tag').before('' +
            '<span class="key-tags" style="display: inline-block">' + $(wrapper).text() + '<i class="fa fa-times remove-tags" onclick="removeIndividualTag(this, \'' + $(wrapper).text() + '\')" aria-hidden="true"></i>' + ' </span>')
    }
}
function removeTags(event, type) {
    $(event).parent().parent().remove();
    addedTypes.splice($.inArray(type, addedTypes), 1);
    if (addedTypes.length < 1) {
        addTypes();
    }
}

function removeIndividualTag(event, type) {
    $(event).parent().remove();
}
