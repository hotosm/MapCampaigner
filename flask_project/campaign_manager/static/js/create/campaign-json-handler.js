function assignCampaignJsonToForm(json) {
    var exceptionNames = ['types_options', 'csrf_token', 'geometry', 'submit'];
    $("input, textarea").each(function (index, element) {
        var inputName = $(element).attr('name');
        if ($.inArray(inputName, exceptionNames) == -1) {
            if (inputName) {
                $(element).val(json[inputName]);
            }
        }
    });

    // render types
    $('#typesTagsContainer').html('');
    selected_types_data = json['types'];
    addMultipleTypes(json['types']);

    // render geometry
    rerender_boundary(json['geometry']);

    // rerender insight function
    function_index = 1;
    $('#insight-function .function-form').html('');
    $.each(json['selected_functions'], function (key, functions) {
        addFunction($('#insight-function-add'), functions);
    });

    // update manager list
    if (jQuery.type(json['campaign_managers']) === "array") {
        managers_list = json['campaign_managers'];
    } else {
        managers_list = [];
    }
    updateManagerList();

    // check types
}

function checkCampaignJsonValue(json) {
    var error = [];

    // check manager list
    if (jQuery.type(json['campaign_managers']) !== "array") {
        error.push('campaign_manager is not list.');
    }


    // check types
    $.each(json['types'], function (key, value) {
        if (!value["type"]) {
            error.push(key + " need 'type' value");
        } else {
            if (jQuery.type(value["type"]) !== "string") {
                error.push('Type of ' + key + ' should be string');
            }
        }
        if (!value["tags"]) {
            error.push(key + " need 'tags' value");
        } else {
            if (jQuery.type(value["tags"]) !== "array") {
                error.push('Tags of ' + key + ' should be array');
            }
        }
    });

    if (error.length > 0) {
        showNotifications(error.join(', '), 'danger');
    }
    return error.length == 0;
}

function checkCampaignJson() {
    clearNotification();
    var campaignJson = $('#advanced-mode-textarea').val();
    try {
        campaignJson = JSON.parse(campaignJson);
        assignCampaignJsonToForm(campaignJson);
        var allValid = checkingAllStep();
        var validWhenAssign = checkCampaignJsonValue(campaignJson);
        if (allValid && validWhenAssign) {
            preparingStep(4);
        }
    } catch (err) {
        showNotifications('Json format is not correct.', 'danger');
    }
}