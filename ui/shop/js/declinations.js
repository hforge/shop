// Add trigger on each select:
// on change we have to check declinations
$("#buy-form select").each(function(){
  $(this).change(function(){
    check_declinations();
  }).trigger('change');
});

function get_selected_purchase_options(){
  // Return dict with purchase options selected by customer
  kw = {}
  $("#buy-form select").each(function(){
    kw[$(this).attr('name')] = $(this).val();
  });
  return kw
}

function get_declination(options){
  for(id_declination in declinations){
    var ok = true;
    declination_options = declinations[id_declination]['option'];
    for(key in declination_options){
      if(options[key] != declination_options[key]){
        ok = false;
      }
    }
    if(ok){
      return id_declination;
    }
  }
}

function check_declinations(){
  options = get_selected_purchase_options();
  id_declination = get_declination(options)
  if(id_declination){
    declination = declinations[id_declination];
    $("#quantity-area").show('slow');
    $("#add-to-cart").show('slow');
    $("#missing-declination").hide('slow');
    $("#price").html(declination['price']);
    $("#weight").html(declination['weight']);
  }else{
    $("#quantity-area").hide('slow');
    $("#add-to-cart").hide('slow');
    $("#missing-declination").show('slow');
    $("#price").html("-");
    $("#weight").html("-");
  }
}

