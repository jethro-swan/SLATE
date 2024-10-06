




# payment to account ----------------------------------------------------------
@app.route("/pay/account", methods=['GET', 'POST'])
def pay_account():
    page = "pay_account"
    mode = "payment"
    #identity_fph = current_user
    #identity_hrns = fph_to_hrns(identity_fph)
    namespace_steward = True
    currency_steward = True
    paying = True
    logged_in = current_user.is_authenticated
    form = PaymentToAccount()
    if form.validate_on_submit():
        flash(
            'Payment submitted to account {}'.format(
                form.to_account_hrns.data,
                form.to_account_fph.data,
                form.amount.data,
                form.annotation.data
            )
        )
        return redirect('/home')
    return render_template(
                "pay_account.html",
                title="Payment to known account",
                form=form,
                logged_in=logged_in,
                page=page,
                mode=mode,
                #identity_type=identity_type,
                #identity_fph=identity_fph,
                #identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward,
                paying=paying
           )
