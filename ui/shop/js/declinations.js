// Add trigger on each select:
// on change we have to check products
$(document).ready(function() {
  $("#quantity").keyup(function(){
     check_products();
  }).trigger('keyup');

  $("#buy-form select").each(function(){
    $(this).change(function(){
      check_products();
    }).trigger('change');
  });

});

function get_selected_purchase_options(){
  // Return dict with purchase options selected by customer
  kw = {};
  $("#buy-form select").each(function(){
    kw[$(this).attr('name')] = $(this).val();
  });
  return kw
}

function get_product(options){
  for(id_product in products){
    if(id_product!='base_product'){
      var ok = true;
      product_options = products[id_product]['option'];
      for(key in product_options){
        if(options[key] != product_options[key]){
          ok = false;
        }
      }
      if(ok){
        return id_product;
      }
    }
  }
}

function get_dict_size(dict){
  var count = 0;
  for (k in dict) count++;
  return count;
}

function check_products(){
  options = get_selected_purchase_options();
  dict_size = get_dict_size(options);
  if(dict_size==0){
    id_product = 'base_product';
  }else{
    id_product = get_product(options);
  }
  if(id_product){
    product = products[id_product];
    $("#quantity-area").show('slow');
    $("#missing-declination").hide('slow');
    $("#price").html(product['price']);
    $("#weight").html(product['weight']);
    if (product['stock'] != null && product['stock'] < $("#quantity").val()){
      $("#out-of-stock").show('slow');
      $("#add-to-cart").hide('slow');
      $("#quantity-in-stock").html(product['stock']);
    }else{
      $("#out-of-stock").hide();
      $("#add-to-cart").show('slow');
    }
  }else{
    $("#out-of-stock").hide();
    $("#quantity-area").hide('slow');
    $("#add-to-cart").hide('slow');
    $("#missing-declination").show('slow');
    $("#price").html("-");
    $("#weight").html("-");
  }
}
