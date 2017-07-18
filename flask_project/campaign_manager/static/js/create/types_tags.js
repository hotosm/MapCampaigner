var addedTypes = [];
var typesOptions = '';

function getTypesSelectionValue() {
    // GET SELECTED TYPES
    var types_value = {};
    $.each(addedTypes, function (index, addedType) {
        if (addedType) {
            types_value['type-' + (index + 1)] = {
                type: addedType,
                tags: []
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

    if (typeof types !== 'undefined') {
        if (types[selected_type]) {
            var tags = types[selected_type]['tags'];
            var key_tags = Object.keys(tags);

            for (var j = 0; j < key_tags.length; j++) {
                div.append('<span class="key-tags" style="display: inline-block">' + key_tags[j] + '<i class="fa fa-times remove-tags" onclick="removeIndividualTag(this, \'' + key_tags[j] + '\')" aria-hidden="true"></i>' + ' </span>');
            }
            div.append('<span style="line-height: 40px;">' + '<button class="btn btn-danger btn-add-tag" type="button" onclick="addTags(this, \'' + selected_type + '\')" style="margin-left: 5px;"><i class="fa fa-plus" style="font-size: 8pt"></i> Add tag</button></span>');
            column.html(div);

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

function addTags(event, type) {
    var tags = types[type]['tags'];
    var key_tags = Object.keys(tags);
    var select_tag = $("<select />");
    select_tag.addClass('select-tag');

    var span_select = $("<span />");
    span_select.addClass('key-tags');
    span_select.html(select_tag);

    for (var j = 0; j < key_tags.length; j++) {
        select_tag.append('<option>' + key_tags[j] + '</option>')
    }
    span_select.append('<i class="fa fa-times remove-tags" onclick="$(this).parent().remove()" aria-hidden="true"></i>');
    $(event).parent().prepend(span_select);
}
