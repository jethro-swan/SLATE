import sys

# SLATE components: -----------------------------------------------------------

#from app.core.list_namespaces import build_namepace_list
from app.core.fph_hrns_maps import hrns_to_fph
#from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import pin_subset_prompt


# Flask components: -----------------------------------------------------------

from flask_wtf import FlaskForm, RecaptchaField
#from flask_wtf import Form ###
from wtforms import StringField, PasswordField, BooleanField, SubmitField
#from wtforms import TextField, TextAreaField, SelectField, RadioField
from wtforms import TextAreaField, SelectField, RadioField, HiddenField
from wtforms import IntegerField, DecimalField, FloatField
from wtforms.validators import DataRequired, InputRequired, Email
from wtforms.validators import Length, EqualTo

# payments --------------------------------------------------------------------

#class PaymentToAccountForm(Form):
class PaymentToAccountForm(FlaskForm):
    to_account_id   = StringField("payee account identifier")
    amount          = StringField(
    #amount          = DecimalField(
    #amount          = FloatField(
    #amount          = IntegerField(
                          "amount",
                          #places=2,
                          validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")


class SpecifyPayeeAccountForm(FlaskForm):
    # This form is used to acquire the payee *account* so a list of suitable
    # payer *accounts* (those in the same *currency*) can be generated from
    # which one can be selected before control is passed to the page handling
    # the /account/<account_fph> endpoint (using the PaymentToAccountForm( )
    # form above,
    to_account_id   = StringField(
                        "payee account identifier",
                        validators=[DataRequired("required")]
                      )
    submit          = SubmitField("list the accounts from which you can pay")


class SpecifyPayeeAgentForm(FlaskForm):
    # This form is used to acquire the payee *account* so a list of suitable
    # payer *accounts* (those in the same *currency*) can be generated from
    # which one can be selected before control is passed to the page handling
    # the /account/<account_fph> endpoint (using the PaymentToAccountForm( )
    # form above,
    to_identity_id  = StringField(
                        "payee agent identifier",
                        validators=[DataRequired("required")]
                      )
    currency_id     = StringField(
                        "currency identifier",
                        validators=[DataRequired("required")]
                      )
    submit          = SubmitField("list the accounts from which you can pay")




class PaymentToIdentityForm(FlaskForm):
    to_id_hrns      = StringField("payee name")
    to_id_fph       = StringField("payee FPH")
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
    currency_name   = StringField(
                        "currency name",
                        validators=[DataRequired("required")]
                      )
    namespace_id    = StringField(
                        "parent namespace",
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
#                            ("trigger", "trigger"),
#                            ("ACP_ratio", "A:C:P ratio")
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
                        "Use currency name by default for initial accounts.",
                        default="checked"
                      )
    acct_id_parent  = BooleanField(
                        "Use identities' namespace for initial accounts.",
                        default="checked"
                      )
    default_account_name = StringField(
                             "Default name for accounts in this currency."
                           )
    acct_immdt_crtn = BooleanField(
                        "Allow immediate creation of an account.",
                        default="checked"
                      )
    create_currency = SubmitField("create currency")

#------------------------------------------------------------------------------

class AccountCreateForm(FlaskForm):
    account_name    = StringField(
                        "account name",
                        validators=[DataRequired("required")]
                      )
    namespace_id    = StringField(
                        "parent namespace",
                        validators=[DataRequired("required")]
                      )
#    owner_id        = StringField(
##                        "account owner",
#                        validators=[DataRequired("required")]
#                      )
    currency_id     = StringField(
                        "account currency",
                        validators=[DataRequired("required")]
                      )
    create_account   = SubmitField("create account")

#------------------------------------------------------------------------------

class NamespaceCreateForm(FlaskForm):
    namespace_name  = StringField(
                        "namespace name",
                        validators=[DataRequired("required")]
                      )
    parent_namespace_id = StringField(
                       "parent namespace identifier",
                       validators=[DataRequired("required")]
                      )
    create_namespace = SubmitField("create namespace")

#------------------------------------------------------------------------------





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

    ##pro_a = pin_random_ord()
    ##pin_prompt = pin_prompt_message(pro_a)

    pin_prompt, pin_subset_indices = pin_subset_prompt()
    pro             = HiddenField(pin_subset_indices)
    #pro             = HiddenField(default=pro_a)
    pse             = PasswordField(
                         pin_prompt,
                         validators=[DataRequired("required")]
                      )

    remember_me     = BooleanField("remember me")
    #recaptcha = RecaptchaField("recaptcha", validators=[DataRequired("required")])
    submit          = SubmitField("log in")

#------------------------------------------------------------------------------
# This form is used to request a login recovery link:

class LoginRecoveryForm(FlaskForm):
    identity        = StringField( # HRNS or FPH
                        "identity",
                        validators=[DataRequired("required")]
                      )
#    fph             = StringField(
#                        "FPH",
#                        validators=[DataRequired("required")]
#                      )
    email           = StringField(
                            "email address",
                            validators=[DataRequired("required"), Email()]
                      )
    submit          = SubmitField("send recovery link")

#------------------------------------------------------------------------------
# This form is reached via the login recovery link requested above. Therefore
# it duplicates some of the elements of the registration form.

class LoginResetForm(FlaskForm):

    password            = PasswordField(
                            "password",
                            validators=[
                                #DataRequired("required")
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
#    ssh_pubkey          = StringField(
#                            "SSH public key"
#                          )

    submit              = SubmitField("register")






#------------------------------------------------------------------------------

class RegistrationForm(FlaskForm):
    # The [username] must be unique within the [namespace] specified:
    username        = StringField(
                        "identity",
                        validators=[DataRequired("required")]
                      )
    #username      = StringField("identity")
    #
    # The [[namespace]] specified must exist already unless the stewards of its
    # most recent ancestor have opted to permit automatic creation of the
    # intermediate namespaces, in which case the initial stewardship of the new
    # namespaces is assigned to those stewards:
    #namespace       = StringField(
    #                    "namespace",
    #                    validators=[DataRequired("required")]
    #                  )

    # The following two are not assigned validators because one or both values
    # may be provided via the URL:
    namespace       = StringField("parent namespace for new user")
    realname        = StringField("real name")
    currency        = StringField("currency for initial account")

    # The drop-down version commented out below works, but is more trouble than
    # it's worth ...
    #test_root = ROOTS + "/4fdcca5ddb678139"
    #namespaces = build_namepace_list(test_root)
    #choices = []
    #for namespace in namespaces:
    #    choices.append((namespace, hrns_to_fph(namespace)))
    #
    #namespace     = SelectField(
    #                    u"choose namespace",
    #                    choices=choices
    #                )
    #
    # Here's the corresponding section cut out of
    #   app/templates/registration.html
    #<p>
    #  <select name="namespace">
    #    {{ form.choices.label }}<br />
    #    {% for choice in form.choices %}
    #      <option value="{{ choice[1] }}">
    #        {{ choice[0] }}
    #      </option>
    #    {% endfor %}
    #  </select>
    #</p>
    #
    # However, a variant of this will be useful for
    # (a) stewards' management of their own namespaces and currencies
    # (b) users' management of their own accounts

    # The [[country]] specified determines certain geographically specific
    # actions or constraints:
#    country         = StringField(
#                        "country"
#                        #"country",
#                        #validators=[DataRequired("required")]
#                       )
    #country       = StringField("country")
    # The [[country]] field will normally be pre-filled from the root namespace
    # specified in [[namespace]] but may be replaced where the substitution is
    # valid (e.g. where a different name is preferred by this identity for the
    # same country - such as "Cymru"|"Wales").
    #
    # NB    THE SET OF FIELDS DISPLAYED HERE WILL DEPEND UPON THE FIELD ABOVE
    #       and the initial set included here is UK-specific.
    #
    #       These fields will not be displayed in all deployments and it is
    #       entirely a matter for the (primary) identity's owner whether or not
    #       to provide such information.
    #
    #       Where such information is provided, it is is the reponsibility of
    #       the stewards of the containing namespace to ensure that these data
    #       are managed in a way compliant with GDPR or whatever other rules
    #       apply locally.
    #
#    county              = StringField("county")
#    town                = StringField("county/city")
#    village             = StringField("village/neighbourhood")
#    bld_number          = StringField("building number")
#    bld_name            = StringField("building name")
#    flat_number         = StringField("flat number")
#    room_number         = StringField("room number")
#    postal_code         = StringField("postcode")
    #
#    grid_ref            = StringField("grid reference")
#    olc                 = StringField("Open Location Code")
#    utm_coord           = StringField("UTM coordinate")
    #
    # Email addresses are not stored by default but the identity's owner may
    # choose to use them to receive notifications:
    #email_1         = StringField("email address 1",
    #                    validators=[DataRequired("required"), Email()])
    email_1             = StringField("email address 1")
#    save_email_1        = BooleanField("save for notifications")
    #email_2         = StringField(
    #                    "email address 2",
    #                    validators=[Email()])
    email_2             = StringField("email address 2")
#    save_email_2        = BooleanField("save for notifications")
    # By default, a hash of the email addressis stored instead. This enables
    # the email addresses to be used for access-recovery purposes.
    #
    # Mobile numbers are not stored by default but the identity's owner may
    # choose to use them to receive notifications (if the stewards of the
    # enclosing namespace allow this. Most will probably not choose to allow
    # SMS to be used for this urpose given that charges will be incurred, but
    # in some cases an arrangement may be made to account for these using one
    # of the identity's local money accounts.
#    phone_1             = StringField("mobile number 1")
    #save_phone_1    = BooleanField("use for notifications")
#    phone_2             = StringField("mobile number 2")
    #save_phone_2    = BooleanField("use for notifications")
    # By default, a hash of the mobile number is stored instead. This enables
    # the mobile number to be used for access-recovery purposes.
    #
#    recovery_a_1        = StringField("recovery answer 1")
    #recovery_q_1   = StringField("")
#    recovery_a_2        = StringField("recovery answer 2")
    #recovery_q_2   = StringField("")
    password            = PasswordField(
                            "password",
                            validators=[
                                #DataRequired("required")
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
#    ssh_pubkey          = StringField(
#                            "SSH public key"
#                          )
    #recaptcha       = RecaptchaField("recaptcha", validators=[DataRequired("required")])
    submit              = SubmitField("register")

#------------------------------------------------------------------------------
# administration --------------------------------------------------------------

#class TQueueForm(FlaskForm):
#    activate_loop   = SubmitField("activate transaction loop")
#    deactivate_loop = SubmitField("deactivate transaction loop")
