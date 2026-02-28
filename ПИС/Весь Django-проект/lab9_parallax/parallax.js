$(window).on("scroll", function() {
    let scrollTop = $(window).scrollTop();
    $(".parallax").css("background-position-y", -(scrollTop * 0.4) + "px");
});
