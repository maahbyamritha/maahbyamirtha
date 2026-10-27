/* Forms work without JavaScript. Update the displayed variant price when available. */
(function () {
  var select = document.getElementById('productVariant');
  var price = document.getElementById('productPrice');
  if (select && price) select.addEventListener('change', function () {
    price.textContent = select.options[select.selectedIndex].dataset.price;
  });
  document.querySelectorAll('.purchase-form, .cart-panel form').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (form.dataset.submitting) { event.preventDefault(); return; }
      form.dataset.submitting = 'true';
      form.setAttribute('aria-busy', 'true');
    });
  });
  window.addEventListener('pageshow', function () {
    document.querySelectorAll('form[data-submitting]').forEach(function (form) {
      delete form.dataset.submitting; form.removeAttribute('aria-busy');
    });
  });
})();
