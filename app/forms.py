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
from wtforms import DateField, DateTimeField
from wtforms.validators import DataRequired, InputRequired, Email
from wtforms.validators import Length, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed

#==============================================================================
# Messaging:

# (1) Agent-to agent or agent-to-community:

class UserMessageForm(FlaskForm):

    # If broadcast box is checked. then for each of the following entity types
    # - *primid*: the message will be sent to that *primid*
    # - *ahid*: the message will be sent the *primid* to which it belongs.
    # - *currency*: the message will be sent to every *account* holder in that
    #   *currency*.
    #
    # If broadcast box is not checked. then any attempt to send to an entity
    # other than an *identity* will be rejected.

    sender          = StringField("Sender")

    recipient       = StringField(
                          "Recipient",
                          validators=[DataRequired("required")]
                      ) # *identity* or *currency*

    broadcast       = BooleanField("Broadcast")

    category        = RadioField(
                        "Category",
                        choices = [
                                    ("payment_received", "payment received"),
                                    ("offer", "offer"),
                                    ("request", "request"),
                                    ("payment_request", "payment request"),
                                    ("event", "event"),
                                    ("other", "other")
                                  ],
                        default = "other"
                      )

    subject         = StringField(
                          "Subject",
                          validators=[DataRequired("required")]
                      )

#    expiry_datetime = DateTimeField(
#                          "Expiry date/time",
#                          format="%Y-%m-%d %H:%M:%S"
#                      )

    expiry_date     = DateField(
                          "Expiry date",
                          format="%Y-%m-%d"
                      )

    lifespan        = IntegerField("Lifespan (days)")

    message_body    = TextAreaField("Message")

    submit          = SubmitField("SEND")

# (2) Steward-to-agent or steward-to-community:

class StewardMessageForm(FlaskForm):

    # If broadcast box is checked. then for each of the following entity types
    # - *primid*: the message will be sent to that *primid*
    # - *ahid*: the message will be sent to *primid* to which it belongs.
    # - *currency*: the message will be sent to the *primid* of each *account*
    #   holder in that *currency*.
    #
    # If broadcast box is not checked. then any attempt to send to an entity
    # other than an *identity* will be rejected.

    recipient       = StringField("Recipient")

    broadcast       = BooleanField("Broadcast to currency/namespace users")

    category        = RadioField(
                        "Subject category",
                        choices = [
                                    ("please_respond", "please respond"),
                                    ("urgent", "urgent"),
                                    ("very_urgent", "very_urgent"),
                                    ("final", "final")
                                  ]
                      )

    subject         = StringField("Subject")

    indelible       = BooleanField("Indelible")

    expiry_datetime = DateField("Date (YYYY-MM-DD)", format="%Y-%m-%d")

    lifespan        = IntegerField("Life-span (days)")

    stewardship_id  = StringField("Stewardship (entity)")

    message_body    = TextAreaField("Message")

    submit          = SubmitField("send")




#==============================================================================

class CSVImportForm(FlaskForm):
#    field_separator = RadioField(
#                        "field separator character",
#                        choices = [
#                                    ("comma", ","),
#                                    ("colon", ":"),
#                                    ("semicolon", ";"),
#                                    ("tab", "tab")
#                                  ]
#                      )
    csv_file        = FileField(
                        "CSV file",
                        validators = [
                            #FileRequired(),
                            FileAllowed(["csv"])
                        ]
                      )
    upload_file     = SubmitField("import dataset")



class FileUploadForm(FlaskForm):
    entity_type     = RadioField(
                        "entity type",
                        choices = [
                                    ("namespaces", "namespaces"),
                                    ("login_identities", "login identities"),
                                    ("aliases", "aliases"),
                                    ("currencies", "currencies"),
                                    ("accounts", "accounts"),
                                    ("payments", "payments")
                                  ]
                      )
    csv_file        = FileField(
                        "CSV file",
                        validators = [
                            #FileRequired(),
                            FileAllowed(["csv"])
                        ]
                      )
    upload_file     = SubmitField("upload CSV file")


# payments --------------------------------------------------------------------

#class PaymentToAccountForm(Form):
class PaymentToAccountForm(FlaskForm):
    to_account_id   = StringField(
                          "payee account",
                          render_kw = { "placeholder":
                                        "payee account identifier"
                                      }
                      )
#   payer_account_fph = RadioField(
#                            "payer account",
#                            choices = []
#                        )
    amount          = StringField(
    #amount          = DecimalField(
    #amount          = FloatField(
    #amount          = IntegerField(
                          "amount",
                          #places=2,
                          validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField(
                          "annotation",
                          render_kw = { "placeholder":
                                        "Enter a short description here"
                                      },
                      )
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


class SpecifyPayeeAgentAndCurrencyForm(FlaskForm):
    to_identity_id  = StringField(
                        "payee agent identifier",
                        validators=[DataRequired("required")]
                      )
    currency_id     = StringField(
                        "currency identifier",
                        validators=[DataRequired("required")]
                      )
    pay_agent       = SubmitField("identify options")


# Added 2025-03-17:
class PayeeCurrencyAmountPaymentForm(FlaskForm):
    to_identity_id  = StringField(
                        "payee agent identifier",
                        validators=[DataRequired("required")]
                      )
    currency_id     = StringField(
                        "currency identifier",
                        validators=[DataRequired("required")]
                      )
    amount          = StringField(
                          "amount",
                          validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")
    # The remaining fields are in the HTML template.









class SelectPayerAndPayeeAccountsForm(FlaskForm):
    payer_account   = RadioField(
                          "select payer account",
                          choices = [],
                          validators=[DataRequired("required")]
                      )
    payee_account   = RadioField(
                          "select payee account",
                          choices = [],
                          validators=[DataRequired("required")]
                      )
    select_accounts = SubmitField("select account pair")











#class PaymentToAccountForm(Form):
class PaymentAccountPairForm(FlaskForm):
    amount          = StringField(
                          "amount",
                          validators=[DataRequired("required")]
                      )
    annotation      = TextAreaField("annotation")
    submit          = SubmitField("pay")
    # The remaining fields are in the HTML template.



class SpecifyPayeeAccountHolderForm(FlaskForm):
    payee_ahid      = StringField(
                          "account-holder identity",
                          render_kw={"placeholder": "payee"},
                          validators=[DataRequired("required")]
                      )
    currency_id     = StringField("currency identifier")
    amount          = DecimalField("amount")
#    amount          = DecimalField(
#                        "amount",
#                        validators=[DataRequired("required")]
#                      )
    annotation      = TextAreaField(
                        "annotation",
                        render_kw={"placeholder": "optional note"}
                      )
    submit          = SubmitField("pay")










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
    submit          = SubmitField("specify payee identity")




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
                        "name",
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
                        "currency prefix symbol",
                        default=""
                      )
    suffix_symbol   = StringField(
                        "currency suffix symbol",
                        default=""
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
                             "Default name for accounts in this currency.",
                             default=""
                           )
    acct_immdt_crtn = BooleanField(
                        "Allow immediate creation of an account.",
                        default="checked"
                      )
    create_currency = SubmitField("create currency")

#------------------------------------------------------------------------------

class AccountCreateForm(FlaskForm):
    account_name    = StringField(
                        "name",
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

class PairingCreateForm(FlaskForm):
    ahid_hrns       = StringField(
                        "account-holder identity",
                        validators=[DataRequired("required")]
                      )
    currency_id     = StringField(
                        "currency",
                        validators=[DataRequired("required")]
                      )
    create_account   = SubmitField("create pairing")


#------------------------------------------------------------------------------

class AccountCreateFormMinimal(FlaskForm):
    currency_id     = StringField(
                        "currency",
                        validators=[DataRequired("required")]
                      )
    create_account   = SubmitField("create pairing")








#------------------------------------------------------------------------------

class NamespaceCreateForm(FlaskForm):
    namespace_name      = StringField(
                            "name",
                            validators=[DataRequired("required")]
                          )
    parent_namespace_id = StringField(
                            "parent namespace",
                            validators=[DataRequired("required")]
                          )
    default_currency_id = StringField(
                            "default currency",
                            render_kw={"placeholder": "currency"}
#                            render_kw={"placeholder": "currency"},
#                            validators=[DataRequired("required")]
                          )
    create_namespace    = SubmitField("create namespace")

#------------------------------------------------------------------------------

class StewardAddForm(FlaskForm):
    new_steward     = StringField(
                        "identity of new steward",
                        render_kw={"placeholder": "identity"},
                        validators=[DataRequired("required")]
                      )
    add_steward     = SubmitField("add steward")

#------------------------------------------------------------------------------

class LoginForm(FlaskForm):

    identity        = StringField("identity")

    email           = StringField("email address")

    pin_prompt, pin_subset_indices = pin_subset_prompt()

    pro             = HiddenField(default=pin_subset_indices)

    pse             = StringField(
                         pin_prompt,
#                         "PIN: ",
                         #render_kw={"autocomplete": "off"},
                         render_kw={"autocomplete": "new-password"},
                         validators=[DataRequired("required")]
                      )

    password        = PasswordField(
                          "password",
                          render_kw={"autocomplete": "on"},
                          validators=[DataRequired("required")]
                      )

    remember_me     = BooleanField("remember me")

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

#    pin                 = PasswordField(
    pin                 = StringField(
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
                        "username",
                        render_kw={"placeholder": "short & simple"},
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
    namespace       = StringField(
                          "parent namespace for username",
                          render_kw={"placeholder": "parent namespace"}
                      )
    realname        = StringField(
                          "real name",
                          render_kw={"placeholder": "Your real name"}
                      )
    currency        = StringField(
                          "currency for new user's initial account",
                          render_kw={"placeholder": "currency identifier"},
                      )

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
    email_1             = StringField(
                              "recovery email address 1",
                              render_kw={"placeholder": "required"},
                              validators=[DataRequired("required")]
                          )
#    save_email_1        = BooleanField("save for notifications")
    #email_2         = StringField(
    #                    "email address 2",
    #                    validators=[Email()])
    email_2             = StringField(
                              "recovery email address 2",
                              render_kw={"placeholder": "(optional)"}
                          )
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
                            render_kw = {"placeholder": "unguessable string"},
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

#    pin                 = PasswordField(
    pin                 = StringField(
                            "PIN",
                            validators=[
                                DataRequired(),
                                Length(min=6, max=6)
                            ],
                            render_kw={"autocomplete": "off"}
                          )
#    ssh_pubkey          = StringField(
#                            "SSH public key"
#                          )
#recaptcha = RecaptchaField("recaptcha", validators=[DataRequired("required")])
    submit              = SubmitField("register")


#==============================================================================
# QR code invitation:

class InvitationQRForm(FlaskForm):

    namespace_id        = StringField(
                              "registration namespace",
                              render_kw={"placeholder": "initial community"}
                          )
    currency_id         = StringField(
                              "currency for new user's initial account",
                              render_kw={"placeholder": "initial currency"},
                          )
    create_invitation   = SubmitField("generate invitation QR code")


#==============================================================================















#------------------------------------------------------------------------------
# administration --------------------------------------------------------------

#class TQueueForm(FlaskForm):
#    activate_loop   = SubmitField("activate transaction loop")
#    deactivate_loop = SubmitField("deactivate transaction loop")
