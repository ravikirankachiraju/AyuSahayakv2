import Slider from "react-slick";
import "./HeroSlider.css";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import { TypeAnimation } from "react-type-animation";

export default function HeroSlider() {
  const settings = {
    dots: true,
    infinite: true,
    autoplay: true,
    autoplaySpeed: 6000,   // stays longer
    speed: 2000,           // smooth slow fade
    slidesToShow: 1,
    slidesToScroll: 1,
    arrows: false,
    fade: true,
    pauseOnHover: false,
  };

  return (
    <section className="hero-slider">
      <Slider {...settings}>

        {/* ✅ Slide 1 */}
        <div className="slide">
          <img src="/slide-3-ayu.png" alt="bg" className="slide-bg" />
          <div className="slide-overlay"></div>

          <div className="slide-content">
            <div className="slide-left">
              <div className="left-bar"></div>

              <div className="slide-left-content">
                <TypeAnimation
                  sequence={[
                    "Welcome to AyuSahayak",
                    2000,
                    "Your trusted healthcare companion",
                    2000,
                  ]}
                  wrapper="h1"
                  speed={60}
                  repeat={Infinity}
                  className="slide-title"
                />

                <p className="slide-text">
                  Your trusted healthcare companion for villages & hospitals.
                </p>

                <ul className="slide-list">
                  <li>Connect with trained nurses</li>
                  <li>Healthcare access for every village</li>
                  <li>Smart doctor–patient bridging</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* ✅ Slide 2 — Typing animation added */}
        <div className="slide">
          <img src="/slide-1-ayu.jpg" alt="bg" className="slide-bg" />
          <div className="slide-overlay"></div>

          <div className="slide-content">
            <div className="slide-left">
              <div className="left-bar"></div>

              <div className="slide-left-content">
                <TypeAnimation
                  sequence={[
                    "Are you an Hospital Owner?",
                    2000,
                    "",
                    200,
                  ]}
                  wrapper="h1"
                  speed={60}
                  repeat={Infinity}
                  className="slide-title"
                />

                <p className="slide-text">
                  Join AyuSahayak today to become part of the fast-evolving
                  medical landscape of Telangana.
                </p>

                <ul className="slide-list">
                  <li>Maximize your earnings.</li>
                  <li>Change the lives of urban Indians.</li>
                  <li>Reliable nurse–doctor coordination</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

{/* ✅ Slide 4 — Village RMP / Quack Awareness */}
<div className="slide">
  <img src="/vilpeo.jpg" alt="bg" className="slide-bg" />
  <div className="slide-overlay"></div>

  <div className="slide-content">
    <div className="slide-left">
      <div className="left-bar"></div>

      <div className="slide-left-content">

        <TypeAnimation
          sequence={[
            "Protect Your Family from RMP Quacks",
            2200,
            "Get Safe, Hospital-Backed Care in Your Village",
            2200,
            "",
            200,
          ]}
          wrapper="h1"
          speed={60}
          repeat={Infinity}
          className="slide-title"
        />

        <p className="slide-text">
          AyuSahayak replaces risky RMP treatments with trained nurses and real doctors,
          ensuring fast, legal, and trusted healthcare for every rural family.
        </p>

        <ul className="slide-list">
          <li>Eliminate dependency on unsafe RMP / quack treatments</li>
          <li>Get real doctors through supervised nurse–doctor telemedicine</li>
          <li>Hospital-backed care delivered safely inside your village</li>
        </ul>

      </div>
    </div>
  </div>
</div>



        {/* ✅ Slide 3 — Typing animation added */}
        <div className="slide">
          <img src="/slide-2-ayu.jpg" alt="bg" className="slide-bg" />
          <div className="slide-overlay"></div>

          <div className="slide-content">
            <div className="slide-left">
              <div className="left-bar"></div>

              <div className="slide-left-content">
                <TypeAnimation
                  sequence={[
                    "Instant Video Consultation",
                    2000,
                    "",
                    200,
                  ]}
                  wrapper="h1"
                  speed={60}
                  repeat={Infinity}
                  className="slide-title"
                />

                <p className="slide-text">
                  Connect patients with nearby hospitals.
                </p>

                <ul className="slide-list">
                  <li>High-quality video calls</li>
                  <li>Quick diagnosis</li>
                  <li>Doctors available anytime</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

      </Slider>
    </section>
  );
}