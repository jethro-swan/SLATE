import sys

# Flask components: -----------------------------------------------------------

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextField, TextAreaField, SelectField, RadioField
from wtforms import IntegerField, DecimalField, HiddenField
from wtforms.validators import DataRequired, InputRequired, Email
from wtforms.validators import Length, EqualTo

# SLATE components: -----------------------------------------------------------

from nests_core.constants import ROOTS
from nests_core.list_namespaces import build_namepace_list
from nests_core.common import hrns_to_fph
from nests_core.auth import pin_random_ord, pin_prompt_message

#------------------------------------------------------------------------------

class RegistrationForm(FlaskForm):
    # The [username] must be a unique HRNS:
    username        = StringField(
                        "identity",
                        validators=[DataRequired("required")]
                      )

    # The following two are not assigned validators because one or both values
    # may be provided via the URL:
    #namespace       = StringField("namespace")
    currency        = StringField("currency")

    # Email addresses are not stored by default but the identity's owner may
    # choose to use them to receive notifications:
    #email_1         = StringField("email address 1",
    #                    validators=[DataRequired("required"), Email()])
    email               = StringField("email address")
    save_email          = BooleanField("save for notifications")
    # A hash of the email addressis stored instead. This enables the email
    # addresses to be used for access-recovery purposes.
    #
    # The user's mobile numbers are not stored as plain text, but a hash of it
    # provides an alternative means to validate an access recovery request.
    phone               = StringField("mobile number")
    #
    recovery_a_1        = StringField("recovery answer 1")
    #recovery_q_1   = StringField("")
    recovery_a_2        = StringField("recovery answer 2")
    #recovery_q_2   = StringField("")
    password            = PasswordField(
                            "password",
                            validators=[
                                InputRequired(),
                                EqualTo(
                                    "password_repeat",
                                    message="Passwords must match"
                                )
                            ]
                          )
    password_repeat     = PasswordField("repeat password")

    pin                 = PasswordField(
                            "PIN",
                            validators=[
                                DataRequired(),
                                Length(min=6, max=6)
                            ]
                          )
    submit              = SubmitField("register")


    #------------------------------------------------------------------------------
    class LoginForm(FlaskForm):
        identity        = StringField(
                            "identity"
        #                    "identity",
        #                    validators=[DataRequired("required")]
                          )
        email           = StringField(
                            "email address"
                          )
        password        = PasswordField("password")
        pro_a = pin_random_ord()
        pin_prompt = pin_prompt_message(pro_a)
        pro             = HiddenField(default=pro_a)
        pse             = PasswordField(
                             pin_prompt,
                            validators=[DataRequired("required")]
                          )
        remember_me     = BooleanField("remember me")
        submit          = SubmitField("log in")

    #------------------------------------------------------------------------------

    class LoginRecoveryForm(FlaskForm):
        identity        = StringField(
                            "identity",
                            validators=[DataRequired("required")]
                          )
        email           = StringField(
                                "email address",
                                validators=[DataRequired("required"), Email()]
                          )
        submit          = SubmitField("send recovery link")

# payments --------------------------------------------------------------------

class PaymentToAccountHRNSForm(FlaskForm):
    to_account_hrns = StringField(
                        "account name",
                        validators=[DataRequired("required")]
                      )
    amount          = DecimalField(
                        "amount",
                        validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")

#class PaymentToAccountFPHForm(FlaskForm):
#    to_account_fph  = StringField("account FPH", validators=[DataRequired("required")])
#    amount          = DecimalField(
#                        "amount",
#                        validators=[DataRequired("required")]
#                      )
#    annotation      = TextAreaField("annotation")
#    submit          = SubmitField("pay")

class PaymentToAccountForm(FlaskForm):
    to_account_hrns = StringField("account name")
#    to_account_fph  = StringField("account FPH")
    amount          = DecimalField(
                        "amount",
                        validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")

class PaymentToIdentityHRNSForm(FlaskForm):
    to_id_hrns      = StringField(
                        "payee name",
                        validators=[DataRequired("required")]
                      )
    #currency_hrns   = StringField("currency name")
    #currency_fph    = StringField("currency FPH")
    amount          = DecimalField(
                        "amount",
                        validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")

#class PaymentToIdentityFPHForm(FlaskForm):
#    to_id_fph       = StringField(
#                        "payee FPH",
#                        validators=[DataRequired("required")]
#                      )
    #currency_hrns   = StringField("currency name")
    #currency_fph    = StringField("currency FPH")
#    amount          = DecimalField(
#                        "amount",
#                        validators=[DataRequired("required")]
#                      )
#    annotation      = TextAreaField("annotation")
#    submit          = SubmitField("pay")

class PaymentToIdentityForm(FlaskForm):
    to_id_hrns      = StringField("payee name")
#    to_id_fph       = StringField("payee FPH")
    currency_hrns   = StringField("currency name")
    currency_fph    = StringField("currency FPH")
    amount          = DecimalField(
                        "amount",
                        validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")

#------------------------------------------------------------------------------

class CurrencyCreateForm(FlaskForm):
    currency_hrns   = StringField(
                        "currency name",
                        validators=[DataRequired("required")]
                      )
#    currency_type   = RadioField(
#                        "currency type",
#                        choices = [
#                            ("money", "money"),
#                            ("scalar", "scalar"),
#                            ("count", "count"),
#                            ("vector", "vector"),
#                            ("matrix", "matrix"),
#                            ("time_series", "time series"),
#                            ("trigger", "trigger")
                            #,
                            #("ACP_ratios", "A:C:P ratio")
#                        ],
#                        validators=[DataRequired("required")]
#                      )
    prefix_symbol   = StringField(
                        "currency prefix symbol"
                      )
    suffix_symbol   = StringField(
                        "currency suffix symbol"
                      )
    # Account creation policies:
    acct_same_name  = BooleanField(
                        "Use currency name for initial accounts.",
                        default="checked"
                      )
    acct_id_parent  = BooleanField(
                        "Use identities' namespace for initial accounts.",
                        default="checked"
                      )
    acct_immdt_crtn = BooleanField(
                        "Allow immediate creation of an account.",
                        default="checked"
                      )
    create_currency = SubmitField("create currency")

#------------------------------------------------------------------------------




#class NamespaceCreateForm(FlaskForm):
#    namespace_hrns   = StringField(
#                        "namespace name",
#                        validators=[DataRequired("required")]
#                      )
#    create_namespace = SubmitField("create namespace")



#------------------------------------------------------------------------------



#------------------------------------------------------------------------------





#------------------------------------------------------------------------------
# administration --------------------------------------------------------------

#class TQueueForm(FlaskForm):
#    activate_loop   = SubmitField("activate transaction loop")
#    deactivate_loop = SubmitField("deactivate transaction loop")
