function assignCampaignJsonToForm(json) {
    var exceptionNames = ['types_options']
    $("input, textarea, select").each(function (index, element) {
        var inputName = $(element).attr('name');
        if ($.inArray(inputName, exceptionNames) >= 0) {
            if (inputName) {
                $(element).val(json[inputName]);
            }
        }
    });
}

function checkCampaignJson() {
    clearNotification();
    var campaignJson = $('#advanced-mode-textarea').val();
    try {
        campaignJson = JSON.parse(campaignJson);
        assignCampaignJsonToForm(campaignJson);

        $("fieldset").each(function (index) {
            checkSteps(index);
        });
        checkFormHeader();
        //preparingStep(4);
    } catch (err) {
        showNotifications('Json format is not correct.', 'danger');
    }
}