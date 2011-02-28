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
       'titleFormat': function(title, currentArray, currentIndex, currentOpts) {
        return '<span>' + (currentIndex + 1) + ' / ' + currentArray.length + (title.length ? ' &nbsp; ' + title : '') + '</span>';
        }
      });
  });
});

