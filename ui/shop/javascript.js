function init_product_gallery(thumb_width, thumb_height, big_width, big_height) {

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
    preview.click(function () {
      // Remove css selected.
      preview_images.removeClass('selected');
      // Add css selected to current image
      $(this).addClass('selected');
      var new_src = $(this).attr('src');
      new_src = new_src.replace(thumb_width_str, big_width_str);
      new_src = new_src.replace(thumb_height_str, big_height_str);
      $('#product-slider-big-img').attr('src', new_src);
    });
  }
}

