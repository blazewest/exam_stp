/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import { formatDate } from "@web/core/l10n/dates";
const { DateTime } = luxon;
const date = DateTime.now()


function handle_picture(files, e) {
    var max_size = 0.0
    $.each(files, function (index, file) {
        var ext = ((file.name).split('.').pop()).toUpperCase();
        var size = parseFloat(file['size']);
        max_size = max_size + size
        if (max_size < 5000000) {
            var reader = new FileReader();
            reader.readAsBinaryString(file);
            reader.onload = function (readerEvt) {
                $('.divFiles').append("<p class='preview_img' data-file_name='" + file.name + "' data-value='" + btoa(readerEvt.target.result) + "' size='" + size + "'><span>" + file.name + "</span> <span class='remove_img fa fa-times-circle'/></p>")
                $(".remove_img").click(function () {
                    $(this).parent(".preview_img").remove();
                });
            }
        } else {
            alert("You can attached files upto 5 MB.");
        }
    });
};


$(document).on("click", '.add_tarveler', function (event) {
    event.preventDefault();
    $('#travellers_modal_new').modal('show');
});

$(document).on("click", '.delete_rec', function (event) {
    event.stopPropagation();
    event.preventDefault();
    $('.del_travellers_modal').modal('show');
    var travell_id = $(this).parent('td').data('traveller_id')
    $('.del_travellers_modal').find("input[name='travell_input_id']").val(travell_id)
});

$(document).on("change", '#time-period', function (event) {
    const customDates = document.getElementById('custom-dates');
    const timePeriodSelect = document.getElementById('time-period');
    const fromDateInput = $('.from-date')
    const toDateInput = $('.to-date')

    if (timePeriodSelect.value !== 'custom-period') {
        fromDateInput.value = '';
        toDateInput.value = '';
    }
    customDates.style.display = timePeriodSelect.value === 'custom-period' ? 'contents' : 'none';
});


// # function to create graphical data in website page
$(document).ready(function () {
    if ($('.passanger_graph_names').val()) {
        var pack_name = $('.passanger_graph_names').val()
        var pass_count = $('.passanger_graph_total_number').val()
        if (pack_name.includes('   ')) {
            var label_list = pack_name.split('   ');
        }
        else {
            var label_list = [pack_name]
        }
        var data = {
            labels: label_list,
            datasets: [{
                label: 'Total Passengers',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                data: JSON.parse(pass_count),
            }]
        };

        var options = {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };
        var ctx = document.getElementById('barChart').getContext('2d');
        var myBarChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: options
        });
    }
    else {
        return false
    }
});

$(document).on("click", '.delete_traveller', function (event) {
    event.preventDefault();
    var tarvel_id = $('.del_travellers_modal').find("input[name='travell_input_id']").val();
    jsonrpc("/delete_traveller", { 'tarvel_id': tarvel_id }).then(function (data) {
        if (data) {
            $('.tarveler_table tr').each(function () {
                if ($(this).attr('data-traveller_id') == tarvel_id) {
                    $(this).remove();
                }
            })
        }
        $('.del_travellers_modal').modal('hide');
    });
});

$(document).on("click", '.save_travellers', function (event) {
    event.preventDefault();
    //        var data=[];
    //        var filename=[];
    //        $('.divFiles .preview_img').each(function(){
    //            var input_val = $(this).data('value');
    //            var file_name = $(this).data('file_name')
    //            data.push(input_val);
    //            filename.push(file_name)
    //        });
    //        $('.img_data').val(data);
    //        $('.img_name').val(filename);
    var visitor = $('.visitor_form');
    var rec = {
        'name': visitor.find('input[name="name"]').val(),
        'gender': visitor.find('select[name="gender"]').val(),
        'age': parseInt(visitor.find('input[name="age"]').val()) || 1,
        //                'identity_type': visitor.find('select[name="identity_type"]').val(),
        //                'identity_number': visitor.find('input[name="identity_number"]').val(),
        //                'img_data': visitor.find('input[name="img_data"]').val(),
        //                'file_name':visitor.find('input[name="file_name"]').val(),
    }
    jsonrpc("/save_traveller", rec).then(function (data) {
        $('.travellers_modal').modal('hide');
        $('.tarveler_table tr:last').after(data);
    });
});

$(document).ready(function () {

    $('.travellers_modal').on('hidden.bs.modal', function () {
        $('.visitor_form').trigger("reset");
        $('.divFiles').children().remove();
    })

    // When choosing an visa, display its required documents
    $("#visa_select").on("change", "select[name='product_id']", function (ev) {
        var payment_id = $(ev.currentTarget).val();
        $('.list_item').addClass("hidden");
        $("#" + payment_id).removeClass("hidden");
    })

    $('[data-toggle="tooltip"]').tooltip();

    $('.cd-filter-block h4').on('click', function () {
        $(this).toggleClass('closed').siblings('.cd-filter-content').slideToggle(300);
    })


    $('.get_return_dt').change(function () {
        var rec = {
            'date': $(this).val(),
            'package': $(this).data('package'),
            'group_package': $('.group_costing').val(),
        }
        jsonrpc("/get_package_data", rec).then(function (data) {
            $('.return_date').val(data['return_date'])
            $('.package_price').html(data['rate'])
            $('.total_price').html(data['total_rate'])
        });

    })

    $('.group_costing').change(function () {
       
            if ($('.travel_date').val()) {
                jsonrpc("/group_costing", {
                'package': $(this).data('package'),
                'date': $('.travel_date').val(),
                'group_package': $(this).val()
            }).then(function (data) {
                $('input[name="adult"]').val(data['adults']);
                $('input[name="children"]').val(data['children']);
                $('.total_price').html(data['rate'])
            });
        } else {
            alert("Please Select Travel Date")
        }
    })


    $('.booking_form').submit(function (e) {
        var rowcount = parseInt($('.tarveler_table tr').length - 1);
        var children = parseInt($('input[name="children"]').val() || 0);
        var adults = parseInt($('input[name="adult"]').val() || 0);
        var infants = parseInt($('input[name="infants"]').val() || 0);
        var total_travellers = parseInt(children + adults + infants);
        if ((rowcount > 0) && (total_travellers == rowcount)) {
            var travellers = []
            $('td.delete_td').each(function () {
                travellers.push($(this).data('traveller_id'))
            });
            $('.travellers').val(travellers);
        } else {
            alert("Please add " + total_travellers + " Travellers Details")
            return false;
        }
    });

    /* -------------- Number validation ---------------*/
    $(".number").keypress(function (e) {
        //if the letter is not digit then display error and don't type anything
        if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57)) {
            //display error message
            $(this).siblings(".errmsg").html("Digits Only").show().fadeOut("3000");
            return false;
        }
    });

    var counter = 1;
    $(".btn-add").on("click", function () {
        var newRow = $("<div>");
        var cols = "";

        cols += '<div class="entry input-group col-xs-3 mt8"><input class="btn" type="file" name="attachment_' + counter + '"/><span class="input-group-btn"><button class="btn ibtnDel" type="button"><span class="fa fa-minus"></span></button></span></div>';
        newRow.append(cols);
        if (counter == 50) $('#addrow').attr('disabled', true).prop('value', "You've reached the limit");
        $("div.controls").append(newRow);
        counter++;
    });
    $("div.controls").on("click", ".ibtnDel", function (event) {
        $(this).closest("div").remove();
        counter -= 1
    });

    $(".show-more a").each(function () {
        var $link = $(this);
        var $content = $link.parent().prev("div.text-content");
        var visibleHeight = $content[0].clientHeight;
        var actualHide = $content[0].scrollHeight - 1;

        if (actualHide > visibleHeight) {
            $link.show();
        } else {
            $link.hide();
        }
    });

    $(".show-more a").on("click", function () {
        var $link = $(this);
        var $content = $link.parent().prev("div.text-content");
        var linkText = $link.text();

        $content.toggleClass("short-text, full-text");

        $link.text(getShowLinkText(linkText));

        return false;
    });

    function getShowLinkText(currentText) {
        var newText = '';

        if (currentText.toUpperCase() === "SHOW MORE") {
            newText = "Show less";
        } else {
            newText = "Show more";
        }

        return newText;
    }
    /*FOR FACILITY ICONS*/

    $(".show-more-facility a").each(function () {
        var $link = $(this);
        var $content = $link.parent().prev("div.text-content-facility");
        var visibleHeight = $content[0].clientHeight;
        var actualHide = $content[0].scrollHeight - 1;

        if (actualHide > visibleHeight) {
            $link.show();
        } else {
            $link.hide();
        }
    });

    $(".show-more-facility a").on("click", function () {
        var $link = $(this);
        var $content = $link.parent().prev("div.text-content-facility");
        var linkText = $link.text();

        $content.toggleClass("short-text-facility, full-text-facility");

        $link.text(getShowLinkText(linkText));

        return false;
    });

    function getShowLinkText(currentText) {
        var newText = '';

        if (currentText.toUpperCase() === "SHOW MORE") {
            newText = "Show less";
        } else {
            newText = "Show more";
        }

        return newText;
    }


    /*=================end===================*/

    $(".package_carousel").owlCarousel({
        loop: true,
        margin: 10,
        nav: true,
        dots: false,
        autoplay: true,
        autoplayTimeout: 2500,
        autoplayHoverPause: true,
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 2
            },
            1000: {
                items: 3
            }
        }
    });
    $('.testimonial_carousel').owlCarousel({
        loop: true,
        margin: 10,
        nav: true,
        dots: false,
        autoplay: true,
        autoplayTimeout: 2500,
        autoplayHoverPause: true,
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 2
            },
            1000: {
                items: 2
            }
        }
    });

    /*============ Date Validation =============*/
    $('.submit_inquiry').click(function (e) {
        var date_pattern1 = "YYYY-MM-DD";
        e.stopPropagation()
        var from = $(".travel_date"),
            to = $(".return_date"),
            date_pattern = formatDate(date),
        date_pattern_wo_zero = date_pattern.replace('MM', 'M').replace('DD', 'D'),
            st_date = moment(from.val(), [date_pattern1,date_pattern, date_pattern_wo_zero], true),
            end_date = moment(to.val(), [date_pattern1,date_pattern, date_pattern_wo_zero], true),
            now = new Date();
        now.setHours(0, 0, 0, 0);
        if ((!st_date.isValid()) || (!end_date.isValid())) {
            var st = st_date.isValid(),
                et = end_date.isValid();
            if (st) {
                from.removeClass('is-invalid');
            } else {
                from.addClass('is-invalid');
            }
            if (et) {
                to.removeClass('is-invalid');
            } else {
                to.addClass('is-invalid');
            }
            alert("Please enter a valid date in the format of " + date_pattern);
            return false;
        }
        else if (Date.parse(from.val()) > Date.parse(to.val())) {
            from.addClass('is-invalid');
            to.addClass('is-invalid');
            alert("Return date should be greater than Travel date");
            return false;
        } else {
            from.removeClass('is-invalid');
            to.removeClass('is-invalid');
            return true;
        }
    });

    $(window).scroll(function () {
        $('#back-to-top').tooltip('hide');
        if ($(this).scrollTop() > 50) {
            $('#back-to-top').fadeIn();
        } else {
            $('#back-to-top').fadeOut();
        }
    });

    $('#back-to-top').click(function () {
        $('#back-to-top').tooltip('hide');
        $('body,html').animate({
            scrollTop: 0
        }, 800);
        return false;
    });
});

