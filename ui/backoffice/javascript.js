$(document).ready(function() {
  $('a[rel="fancybox"]').each(function(){
    $(this).fancybox(
      {'titlePosition': 'inside',
       'transitionIn'  : 'elastic',
       'transitionOut'  : 'elastic',
       'changeSpeed': 0,
       'changeFade': 0,
       'overlayColor': '#000',
       'overlayOpacity': 0.6,
       'hideOnContentClick': true,
      });
  });
});

