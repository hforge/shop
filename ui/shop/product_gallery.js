function init_product_gallery(thumb_width, thumb_height, big_width, big_height,
                              change_on_click, has_loupe, activate_lightbox) {

  var preview_images = $('#product-slider-box .product-slider-preview-img');
  var size = preview_images.size();

  // Remove css selected.
  preview_images.removeClass('selected');
  // Initialize css for the current image
  $(preview_images[0]).addClass('selected');

  thumb_width_str = "width=" + thumb_width;
  thumb_height_str = "height=" + thumb_height;
  big_width_str = "width=" + big_width;
  big_height_str = "height=" + big_height;

  for (i=0; i<size; i++) {
    preview = $(preview_images[i]);
    if (change_on_click == true){
      preview.click(function (){
          set_as_big_thumb($(this), preview_images, thumb_width_str, thumb_height_str, big_width_str, big_height_str, has_loupe)
      });
    }else{
      preview.hover(function (){
          set_as_big_thumb($(this), preview_images, thumb_width_str, thumb_height_str, big_width_str, big_height_str, has_loupe)
      });
    }
  }

  if(has_loupe == true){
    $('#product-slider-big-a').loupe();
  }else{
    $('#product-slider-big-a').removeAttr('href');
  }

  // Lighbox
  if (activate_lightbox == true){
    $(".product-slider-preview-a").fancybox(
      {'titlePosition': 'inside',
       'transitionIn'  : 'elastic',
       'transitionOut'  : 'elastic',
       'overlayColor': '#000',
       'overlayOpacity': 0.6,
       'hideOnContentClick': true,
       'titleFormat': function(title, currentArray, currentIndex, currentOpts) {
        return '<span>' + (currentIndex + 1) + ' / ' + currentArray.length + (title.length ? ' &nbsp; ' + title : '') + '</span>';
        }
      });

    $("#product-slider-big-a").click(function() {
      $(".product-slider-preview-a:first").trigger('click');
      return false;
    });
  }else{
    $('.product-slider-preview-a').each(function(){
      $(this).removeAttr('href');
    });
  }

}

function set_as_big_thumb(e, preview_images, thumb_width_str, thumb_height_str, big_width_str, big_height_str, has_loupe){
  // Remove css selected.
  preview_images.removeClass('selected');
  // Add css selected to current image
  e.addClass('selected');
  var new_src = e.attr('src');
  new_src = new_src.replace(thumb_width_str, big_width_str);
  new_src = new_src.replace(thumb_height_str, big_height_str);
  $('#product-slider-big-img').attr('src', new_src);
  // Change href
  if(has_loupe == true){
    href = new_src.replace(';thumb?', ';download');
    href = href.replace(big_width_str, '');
    href = href.replace(big_height_str, '');
    href = href.replace('&', '');
    $('#product-slider-big-a').attr('href', href);
    $('#product-slider-big-a').loupe();
  }else{
    $('#product-slider-big-a').attr('href', '');
  }
}
