
# import flask framework. g stands for global allows us to use other variable in the project
from flask import Flask, g, request
from flask import render_template, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_bcrypt import check_password_hash
import datetime
import os

import models
import forms
import stripe

DEBUG = True
PORT = 8000

stripe_keys = {
  'secret_key':['sk_test_w7VS3zlXS8nbev96CqZyH5C700lNmo9fP0'],
  'publishable_key':['pk_test_0ZSmd03Ao5L3zGGWFPb784cH00jsfe5W5S']
}

stripe.api_key = stripe_keys['secret_key']

app = Flask(__name__)
app.secret_key = "peonies"

# setup login_manager with LoginManager class
login_manager = LoginManager()
# setup login_manager to work with our app
login_manager.init_app(app)
# if a user is not logged in, redirect them to login view
login_manager.login_view = 'login'

def cart_quantity(user):
    order= models.Order.select().where(models.Order.user_id ==user.id, models.Order.purchased == False).get()
    cartq = 0
    cart = models.OrderDetails.select().where(models.OrderDetails.order_id == order)
    for item in cart:
        cartq += item.quantity
    return cartq


@login_manager.user_loader
def load_user(userid):
    try: 
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    """Connect to the database before each request"""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user

@app.after_request
def after_request(response):
    """Close the database after each connection requesst and send through the response"""
    g.db.close()
    return response

@app.route('/')
def index():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    featured=models.Product.select().order_by(models.Product.average_rating.desc()).limit(4)
    return render_template("index.html", featured=featured, cartq=cartq)

@app.route('/quiz')
def quiz():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    return render_template("quiz.html", cartq=cartq)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash('This email does not exist.')
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)    # creates a session and logs in the user
                flash('You have been logged in!', 'success')
                order = models.Order.select().where(models.Order.user == user.id, models.Order.purchased==False)
                if order.exists():
                    return redirect(url_for('shop'))
                else:
                    newOrder = models.Order.create_order(user=user)
                    return redirect(url_for('shop'))
            else:
                flash('Email or password incorrect.', 'danger')
    return render_template("login.html", form=form, cartq=cartq)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = forms.RegisterForm()
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    # when the form is validated and submitted, create a new user
    if form.validate_on_submit():
        models.User.create_user(
            fname=form.fname.data,
            lname=form.lname.data,
            email=form.email.data,
            password=form.password.data
        )
        user = models.User.get(models.User.email== form.email.data)
        models.Order.create_order(user=user)
        login_user(user)
        # redirect user to index
        flash('Congratulations! You signed up!', 'success')
        return redirect(url_for('shop'))
    return render_template("signup.html", form=form, cartq=cartq)

@app.route('/logout')
# from login_manager login view, will redirect you to the login page
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

def time_of_day(hour):
    return (
        "morning" if 5 <= hour <= 11
        else
        "afternoon" if 12 <= hour <= 17
        else
        "evening" if 18 <= hour <= 22
        else
        "night"
    )

@app.route('/profile')
@login_required
def profile():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    return render_template("dashboard.html", user=user, greeting=greeting, cartq=cartq)

@app.route('/profile/edit', methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    form = forms.EditProfileForm()
    if form.validate_on_submit():
        user.fname=form.fname.data
        user.lname=form.lname.data
        user.email=form.email.data
        user.save()
        return redirect(url_for("profile"))
    return render_template("editProfile.html", form=form, user=user, greeting=greeting, cartq=cartq)

@app.route('/profile/address', methods=["GET", "POST"])
@login_required
def edit_address():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    form = forms.EditAddressForm()
    if form.validate_on_submit():
        user.street_address=form.street_address.data
        user.city=form.city.data
        user.state=form.state.data
        user.postal_code=form.postal_code.data
        user.save()
        return redirect(url_for("profile"))
    return render_template("editAddress.html", form=form, user=user, greeting=greeting, cartq=cartq)


@app.route('/profile/orders', methods=["GET"])
@login_required
def order_history():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    orders = models.Order.select().where(models.Order.user_id == user.id, models.Order.purchased == True)
    return render_template("orderHistory.html", user=user, greeting=greeting, orders=orders, cartq=cartq)

@app.route('/profile/orders/view_details/<orderid>', methods=["GET"])
@login_required
def view_details(orderid):
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    order = models.Order.get(models.Order.id == orderid)
    print(order)
    details = models.OrderDetails.select().where(models.OrderDetails.order_id == orderid)
    return render_template("viewDetails.html", user=user, greeting=greeting, order=order, details=details, cartq=cartq)

@app.route('/profile/reviews', methods=["GET"])
@login_required
def reviews():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    reviews = models.Review.select().where(models.Review.user_id == user.id).order_by(models.Review.date_posted.desc())
    return render_template("reviews.html", user=user, greeting=greeting, reviews=reviews, cartq=cartq)

@app.route('/profile/reviews/review_details/<reviewid>', methods=["GET"])
@login_required
def review_details(reviewid):
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    current_hour = datetime.datetime.now().hour
    greeting = time_of_day(current_hour)
    review = models.Review.get(models.Review.id == reviewid)
    return render_template("reviewDetails.html", user=user, greeting=greeting, review=review, cartq=cartq)

@app.route('/<origin>/delete_review/<reviewid>', methods=["GET", "DELETE", "PUT"])
@login_required
def delete_review(origin, reviewid):
    try:
        delete_review = models.Review.get(models.Review.id == reviewid)
    except:
        raise Exception("delete review error")
    if delete_review:
        print("this review's rating", delete_review.rating)
        product = models.Product.get(models.Product.id == delete_review.product_id)
        print("current product average", product.average_rating)
        delete_review.delete_instance()
        reviews = models.Review.select().where(models.Review.product_id == product.id)
        avg = "%.2f" % average(reviews)
        print("variable avg",avg)
        product.average_rating = avg
        product.save()
        print("new product average", product.average_rating)
        if origin == "profile":
            return redirect(url_for('reviews'))
        else:
            return redirect(url_for("product_details", data_name=origin))
    else:
        return("error")

@app.route('/<origin>/edit_review/<reviewid>', methods=["GET", "POST"])
@login_required
def edit_review(origin, reviewid):
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    form = forms.EditReviewForm()
    review = models.Review.get(models.Review.id == reviewid)
    product = models.Product.get(models.Product.id == review.product_id)
    reviews = models.Review.select().where(models.Review.product_id == product.id)
    if form.validate_on_submit():
        print("validated")
        review.title = form.title.data
        review.rating = form.rating.data
        review.content = form.content.data
        review.save()
        avg = "%.2f" % average(reviews)
        product.average_rating = avg
        product.save()
        if origin == "profile":
            return redirect(url_for('reviews'))
        else:
            return redirect(url_for("product_details", data_name=origin))
    return render_template("editReview.html", form=form, cartq=cartq)


@app.route('/shop', methods=["GET"])
@login_required
def shop():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    product = models.Product.select()
    return render_template("products.html", product=product, cartq=cartq)

def average(reviews):
    ratings = []
    for review in reviews:
        print("from average(), ratings", review.rating)
        ratings.append(review.rating)
    if len(ratings)==0:
        return 0
    return sum(ratings)/len(ratings)

@app.route('/shop/<category>', methods=["GET"])
@login_required
def shop_products(category):
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    product = models.Product.select(models.Product).join(models.Category).where(models.Category.category_name == category)
    return render_template("products.html", product=product, cartq=cartq)

@app.route('/shop/product/<data_name>', methods=["GET", "POST"])
@login_required
def product_details(data_name):
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    form = forms.ReviewForm()
    user = current_user
    product = models.Product.get(models.Product.data_name == data_name)
    reviews = models.Review.select().where(models.Review.product_id == product.id).order_by(models.Review.date_posted.desc())
    if form.validate_on_submit():
        models.Review.create(
            user=user.id,
            product=product,
            title=form.title.data,
            rating=form.rating.data,
            content=form.content.data
        )
        avg = "%.2f" % average(reviews)
        product.average_rating = avg
        product.save()
        return redirect(url_for("product_details", data_name=data_name))
    # print(product)
    return render_template("productDetails.html", product=product, form=form, reviews=reviews, cartq=cartq)

@app.route('/rating_votes/<productid>', methods=["GET"])
def rating_votes(productid):
    reviews = models.Review.select().where(models.Review.product_id == productid)
    count_5 = 0
    count_4 = 0
    count_3 = 0
    count_2 = 0
    count_1 = 0
    for review in reviews:
        print(review.rating)
        if review.rating == 5:
            count_5 += 1
        elif review.rating == 4:
            count_4 += 1
        elif review.rating == 3:
            count_3 += 1
        elif review.rating == 2:
            count_2 += 1
        elif review.rating == 1:
            count_1 += 1
    data = [count_5,count_4,count_3,count_2,count_1]
    print(data)
    return str(data)


def increment_total(price):
    user = current_user
    order = models.Order.select().where(models.Order.user == user.id, models.Order.purchased==False).get()
    order.total_cost += price
    order.save()

def decrement_total(price):
    user = current_user
    order = models.Order.select().where(models.Order.user == user.id, models.Order.purchased==False).get()
    order.total_cost -= price
    order.save()

@app.route('/<origin>/add_to_cart/<productid>', methods=["GET", "POST", "PUT"])
@app.route('/<origin>/add_to_cart/<productid>/<orderid>', methods=["GET", "POST", "PUT"])
@login_required
def add_to_cart(origin, productid, orderid=None):
    user = current_user
    order = models.Order.select(models.Order.id).where(models.Order.user == user.id, models.Order.purchased==False)
    order_details = models.OrderDetails.select(models.Product, models.OrderDetails).join(models.Product).where(models.OrderDetails.order_id == order, models.OrderDetails.product_id == productid)
    if order_details.exists():
        existing_order_details = order_details.get()
        existing_order_details.quantity += 1
        existing_order_details.subtotal += existing_order_details.product.price
        existing_order_details.save()
        increment_total(existing_order_details.product.price)
        flash('Added to your cart!', 'success')
        if origin == "cart":
            return redirect(url_for("cart"))
        elif origin == "order":
            return redirect(url_for('view_details', orderid=orderid))
        else:
            return redirect(url_for('product_details', data_name=origin))
    else:
        user = current_user
        product = models.Product.select().where(models.Product.id == productid).get()
        order = models.Order.select().where(models.Order.user == user.id, models.Order.purchased==False).get()
        try:
            models.OrderDetails.create_order_details(order.id, product.id, product.price)
            increment_total(product.price)
            flash('Added to your cart!', 'success')
            if origin == "cart":
                return redirect(url_for("cart"))
            elif origin == "order":
                return redirect(url_for('view_details', orderid=orderid))
            else:
                return redirect(url_for('product_details', data_name=origin))
        except:
            raise Exception("failed to add to cart")

@app.route('/subtract_from_cart/<order_details_id>', methods=["GET", "PUT"])
@login_required
def subtract_from_cart(order_details_id):
    order_details = models.OrderDetails.select().where(models.OrderDetails.id == order_details_id)
    if order_details.exists():
        existing_order_details = order_details.get()
        if existing_order_details.quantity > 1:
            existing_order_details.quantity -= 1
            existing_order_details.subtotal -= existing_order_details.product.price
            existing_order_details.save()
            decrement_total(existing_order_details.product.price)
            flash('Removed from your cart.', 'danger')
            return redirect(url_for("cart"))
        else:
            decrement_total(existing_order_details.product.price)
            existing_order_details.delete_instance()
            flash('Removed from your cart.', 'danger')
            return redirect(url_for("cart"))
    else:
        flash("there was an error with this request")

@app.route('/remove_from_cart/<order_details_id>', methods=["GET", "DELETE"])
@login_required
def remove_from_cart(order_details_id):
    try:
        remove_order = models.OrderDetails.get(models.OrderDetails.id == order_details_id)
    except:
        raise Exception("remove from cart error")
    if remove_order:
        remove_order.order.total_cost -= remove_order.subtotal
        remove_order.order.save()
        remove_order.delete_instance()
        flash('Removed from your cart.', 'success')
        return redirect(url_for("cart"))
    else:
        return ("error")

@app.route('/cart', methods=["GET"])
@login_required
def cart():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    order = models.Order.select().where(models.Order.user == user.id, models.Order.purchased==False).get()
    cart = models.OrderDetails.select().where(models.OrderDetails.order_id == order.id)
    
    return render_template("cart.html", cart=cart, order=order, cartq=cartq)

@app.route('/shipping', methods=["GET", "POST"])
@login_required
def shipping():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    form = forms.ShippingForm()
    user = current_user
    order = models.Order.get(models.Order.user_id == user.id, models.Order.purchased == False)
    if form.validate_on_submit():
        order.recipient_fname=form.recipient_fname.data
        order.recipient_lname=form.recipient_lname.data
        order.recipient_street_address=form.recipient_street_address.data
        order.recipient_city=form.recipient_city.data
        order.recipient_state=form.recipient_state.data
        order.recipient_postal_code=form.recipient_postal_code.data
        order.save()
        return redirect("payment")
    return render_template("shipping.html", order=order, form=form, cartq=cartq)


@app.route('/payment', methods=["GET", "POST"])
@login_required
def payment():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    form = forms.EditAddressForm()
    user = current_user
    if form.validate_on_submit():
        user.street_address=form.street_address.data
        user.city=form.city.data
        user.state=form.state.data
        user.postal_code=form.postal_code.data
        user.save()
        return redirect("confirm_order")
    return render_template("payment.html", user=user, form=form, cartq=cartq)

@app.route('/confirm_order', methods=["GET","POST"])
@login_required
def confirm_order():
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    order = models.Order.select().where(models.Order.user == user.id, models.Order.purchased==False).get()
    cart = models.OrderDetails.select().where(models.OrderDetails.order_id == order.id)
    return render_template("confirmation.html", user=user, order=order, cart=cart, key=stripe_keys["publishable_key"], cartq=cartq)


@app.route('/checkout', methods=["GET", "PUT", "POST"])
@login_required
def checkout():
    user = current_user
    order = models.Order.get(models.Order.user_id == user.id, models.Order.purchased == False)
    print(order.purchased)
    order.purchased = True
    order.order_date = datetime.datetime.now()
    order.save()
    models.Order.create_order(user=user.id)
    return redirect(url_for("thank_you", orderid=order.id))

@app.route('/thank_you/<orderid>', methods=["GET", "PUT"])
@login_required
def thank_you(orderid):
    if current_user.is_authenticated:
        user=current_user
        cartq = cart_quantity(user)
    else:
        cartq=0
    user = current_user
    order = models.Order.get(models.Order.id == orderid)
    cart = models.OrderDetails.select().where(models.OrderDetails.order_id == orderid)
    return render_template("thankyou.html", user=user, order=order, cart=cart, cartq=cartq)

if __name__ == '__main__':
    models.initialize()
    # try:
    #     bouquet= models.Category.get(models.Category.id ==1)
    #     plant = models.Category.get(models.Category.id ==2)
    #     models.Product.create(
    #         name="Declare Your Love",
    #         description="Tulips continue blooming even after they are cut, which is perfect for their meaning: declaration of love. They reach out as if eagerly declaring their love. If you want to be assertive in your feelings, this is the perfect arrangement.",
    #         image="https://i.ibb.co/xfF5xJY/tulip.png",
    #         plant="tulip",
    #         meaning="declaration of love",
    #         price=38,
    #         data_name="declare-your-love",
    #         category=bouquet
    #     )
    #     models.Product.create(
    #         name="Striped Carnation",
    #         description="The striped carnation means I cannot be with you. Let someone down easy with a beautiful bloom that will reject them for you. You may also consider sending them a note along with it.",
    #         image="https://i.ibb.co/H2mwdfb/carnation.jpg",
    #         plant="striped carnation",
    #         meaning="I cannot be with you",
    #         price=35,
    #         data_name="striped-carnation",
    #         category=bouquet
    #     )
    #     models.Product.create(
    #         name="Radiant Charms",
    #         description="Tulips and ranunculus combine to create a beautiful bouquet and a sweet message. Tulips mean declaration of love and ranunuculus is for you are radiant with charms. The reciever of this arrangement is sure to be stunned by its beauty.",
    #         image="https://i.ibb.co/s3JKp2S/tulips-and-ranunculus.jpg",
    #         plant="tulip, ranunculus",
    #         meaning="declaration of love, you are radiant with charms",
    #         price=42,
    #         data_name="radiant-charms",
    #         category=bouquet
    #     )
    #     models.Product.create(
    #         name="Roses and Carnations",
    #         description="This bouquet is a perfect message for a lasting love. Red roses mean love and pink carnation means I will never forget you.",
    #         image="https://i.ibb.co/frVvkV8/roses-carnation.jpg",
    #         plant="red rose, pink carnation",
    #         meaning="love, I will never forget you",
    #         price=40,
    #         data_name="roses-and-carnation",
    #         category=bouquet
    #     )
    #     models.Product.create(
    #         name="New Beginnings",
    #         description="Seeing these sunny flowers signals a new beginning. They are perfect for the springtime and weddings to mark the beginning of a new chapter.",
    #         image="https://i.ibb.co/K77FPfK/daffodil.jpg",
    #         plant="daffodil",
    #         meaning="new beginnings",
    #         price=35,
    #         data_name="new-beginnings",
    #         category=bouquet
    #     )
    #     models.Product.create(
    #         name="Forgive Me",
    #         description="This is the perfect arrangement if you seek forgiveness. Make your apologies with purple hyacinth, please forgive me, and you are sure to be forgiven.",
    #         image="https://i.ibb.co/1nxvMbw/purple-hyacinth.jpg",
    #         plant="purple hyacinth",
    #         meaning="please forgive me",
    #         price=47,
    #         data_name="forgive-me",
    #         category=bouquet
    #     )
    #     models.Product.create(
    #         name="Always Ivy",
    #         description="This hardy plant is easy to care for and its meaning fits it well: fidelity. This ivy will be with you as long as you care for it. It also makes a thoughtful gift for a plant loving partner or friend.",
    #         image="https://i.ibb.co/30KLRZv/ivy.jpg",
    #         plant="ivy",
    #         meaning="fidelity",
    #         price=14,
    #         data_name="always-ivy",
    #         category=plant
    #     )
    #     models.Product.create(
    #         name="Aloe",
    #         description="If you need someone to know you are not in high spirits, aloe will convey the message you want to send. Aloe means grief, and any receivers are sure to understand your pain.",
    #         image="https://i.ibb.co/VwMW9w1/aloe.jpg",
    #         plant="aloe",
    #         meaning="grief",
    #         price=15,
    #         data_name="aloe",
    #         category=plant
    #     )
    #     models.Product.create(
    #         name="Peppermint",
    #         description="This well loved herb is sure to make you feel warm inside. Peppermint means warmth of feeling. This is a comforting message if someone is in an unfamiliar place, and makes a lovely tea.",
    #         image="https://i.ibb.co/16ZjBKt/peppermint.jpg",
    #         plant="peppermint",
    #         meaning="warth of feeling",
    #         price=12,
    #         data_name="peppermint",
    #         category=plant
    #     )
    # except ValueError:
    #     pass
    app.run(debug=DEBUG, port=PORT)
