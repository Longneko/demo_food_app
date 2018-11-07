// Get page name
var path = window.location.pathname;
var page = path.split("/").pop();

// Set type of object to be edited in forms
var obj_type;
switch(page) {
    case "allergies":
        obj_type = "allergy";
        break;
    case "ingredient_categories":
        obj_type = "ingredient_category";
        break;
    case "ingredients":
        obj_type = "ingredient";
        break;
    case "recipes":
        obj_type = "recipe";
        break;
}

// Set form element to default state based on its type and data-default if provided
function set_default(element) {
    var type;
    switch($(element).prop('nodeName')) {
        case "SELECT":
            type = "select";
            break
        case "TEXTAREA":
            type = "textarea";
            break
        case "INPUT":
            type = $(element).attr("type");
            break
        default:
            return false;
    }

    var default_val;
    try {
        default_val = $(element).data("default");
    } catch (err) {
        default_val = "";
    }

    if ( ["select", "textarea", "text", "number", "email", "url"].includes(type) ) {
        $(element).val(default_val);
    }
    if ( type == "checkbox" ) {
        $(element).prop("checked", Boolean(default_val));
    }
}

// Get object from DB asynchronously and execute provided func on success
function fetch_object(obj_type, db_id, success) {
    var params = {
        "obj_type": obj_type,
        "db_id": db_id,
    }
    var url = window.location.origin + "/json"

    $.getJSON(url, params, function(data) {
        return success(data);
    });
}

// Sets basic form values to default from data-default if possible
function form_set_new(form_id) {
    var form_elements = $("[form="+ form_id + "]");

    set_default(form_elements.filter("[name=db_id]"));
    set_default(form_elements.filter("[name=name]"));
}

// Sets form values to those of the object under editing
function form_set_edit(form_id, db_id, data=null) {
    if ( data ) {
        var form_elements = $("[form="+ form_id + "]");

        form_elements.filter("[name=db_id]").val(data["db_id"]);
        form_elements.filter("[name=name]").val(data["name"]);
    } else {
        form_set_new(form_id);
        fetch_object(obj_type, db_id, function(obj) {
            form_set_edit(form_id, db_id, obj);
        });
    }
}


$(document).ready(function() {
    // On new popluate the form with default values
    $(".trigger-form-new").click(function() {
        var modal_id = $(this).data("target");
        var form_id = $(modal_id).find("form").attr("id")
        form_set_new(form_id);
    });

    // On edit popluate form with values of the entry under editing
    $(".trigger-form-edit").click(function() {
        var modal_id = $(this).data("target");
        var form_id = $(modal_id).find("form").attr("id")

        var db_id = $(this).data("db_id");
        form_set_edit(form_id, db_id);
    });

    // Focus on Name field when modal window is shown
    $("#modal-form").on("shown.bs.modal", function() {
        $(this).find("input[name=name]").focus();
    });
});
