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
}

function checkCampaignJson() {
    clearNotification();
    var campaignJson = $('#advanced-mode-textarea').val();
    try {
        campaignJson = JSON.parse(campaignJson);
        assignCampaignJsonToForm(campaignJson);
        var allValid = checkingAllStep();
        if (allValid) {
            preparingStep(4);
        }
    } catch (err) {
        showNotifications('Json format is not correct.', 'danger');
    }
}