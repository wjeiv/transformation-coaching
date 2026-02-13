import React, { useState } from "react";
import { Link } from "react-router-dom";
import { publicAPI } from "../services/api";
import toast from "react-hot-toast";

const LandingPage: React.FC = () => {
  const [contactForm, setContactForm] = useState({
    name: "",
    email: "",
    phone: "",
    message: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleContact = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await publicAPI.submitContact(contactForm);
      toast.success("Thank you! We'll be in touch soon.");
      setContactForm({ name: "", email: "", phone: "", message: "" });
    } catch {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-dragonfly-dark via-dragonfly to-brand-600 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 800 600" fill="none">
            <ellipse cx="400" cy="120" rx="40" ry="55" fill="white" opacity="0.3" />
            <ellipse cx="340" cy="160" rx="90" ry="30" fill="white" opacity="0.15" transform="rotate(-20 340 160)" />
            <ellipse cx="460" cy="160" rx="90" ry="30" fill="white" opacity="0.15" transform="rotate(20 460 160)" />
            <ellipse cx="330" cy="120" rx="75" ry="25" fill="white" opacity="0.1" transform="rotate(-35 330 120)" />
            <ellipse cx="470" cy="120" rx="75" ry="25" fill="white" opacity="0.1" transform="rotate(35 470 120)" />
            <line x1="400" y1="175" x2="400" y2="400" stroke="white" strokeWidth="4" opacity="0.15" />
          </svg>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32 relative">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
              Transform Your Life Through{" "}
              <span className="text-brand-200">Purposeful Training</span>
            </h1>
            <p className="text-lg sm:text-xl text-white/80 mb-8 leading-relaxed">
              Personalized coaching that meets you where you are and guides you to where you want to be.
              Whether you're training for your first 5K or your next Ironman, we'll help you unlock your potential.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/register"
                className="inline-flex items-center justify-center rounded-lg bg-white text-dragonfly-dark px-8 py-4 text-base font-semibold shadow-lg hover:bg-gray-100 transition-all"
              >
                Start Your Transformation
              </Link>
              <a
                href="#contact"
                className="inline-flex items-center justify-center rounded-lg border-2 border-white/30 px-8 py-4 text-base font-semibold hover:bg-white/10 transition-all"
              >
                Learn More
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Our Mission
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed">
              At Transformation Coaching, we believe that every person has the power to transform.
              Like the dragonfly — a symbol of change, adaptability, and self-realization — we guide
              our athletes through their own metamorphosis. Our coaching is built on science, driven
              by passion, and tailored to your unique journey.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="card text-center hover:shadow-md transition-shadow">
              <div className="w-14 h-14 bg-dragonfly/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-dragonfly" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg mb-2">Personalized Plans</h3>
              <p className="text-gray-600 text-sm">
                Every workout is crafted specifically for you — your goals, your schedule, your abilities.
                No cookie-cutter programs here.
              </p>
            </div>

            <div className="card text-center hover:shadow-md transition-shadow">
              <div className="w-14 h-14 bg-brand-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg mb-2">Garmin Integration</h3>
              <p className="text-gray-600 text-sm">
                Workouts sync directly to your Garmin device. Your coach creates the plan,
                and it appears on your watch — seamless and effortless.
              </p>
            </div>

            <div className="card text-center hover:shadow-md transition-shadow">
              <div className="w-14 h-14 bg-purple-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg mb-2">Dedicated Support</h3>
              <p className="text-gray-600 text-sm">
                Your coach is with you every step of the way. Regular check-ins, plan adjustments,
                and the accountability you need to succeed.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Sports Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-12">
            Training For Every Discipline
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: "Running", icon: "🏃", desc: "From 5K to ultra-marathon" },
              { name: "Cycling", icon: "🚴", desc: "Road, gravel, and mountain" },
              { name: "Swimming", icon: "🏊", desc: "Pool and open water" },
              { name: "Strength", icon: "💪", desc: "Functional and sport-specific" },
            ].map((sport) => (
              <div
                key={sport.name}
                className="card text-center hover:shadow-md hover:-translate-y-1 transition-all cursor-default"
              >
                <div className="text-4xl mb-3">{sport.icon}</div>
                <h3 className="font-semibold text-lg mb-1">{sport.name}</h3>
                <p className="text-gray-500 text-sm">{sport.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: "1", title: "Sign Up", desc: "Create your free account and choose your coach" },
              { step: "2", title: "Connect Garmin", desc: "Link your Garmin Connect account for seamless sync" },
              { step: "3", title: "Get Your Plan", desc: "Your coach creates personalized workouts for you" },
              { step: "4", title: "Train & Transform", desc: "Import workouts to your watch and start training" },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 bg-dragonfly text-white rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-lg">
                  {item.step}
                </div>
                <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                <p className="text-gray-600 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Ready to Transform?
            </h2>
            <p className="text-lg text-gray-600">
              Reach out and let's talk about your goals. No commitment, just a conversation.
            </p>
          </div>

          <form onSubmit={handleContact} className="card space-y-5">
            <div className="grid sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  required
                  className="input-field"
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  placeholder="Your name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  required
                  className="input-field"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  placeholder="you@example.com"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone (optional)</label>
              <input
                type="tel"
                className="input-field"
                value={contactForm.phone}
                onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
                placeholder="(555) 123-4567"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
              <textarea
                required
                rows={4}
                className="input-field resize-none"
                value={contactForm.message}
                onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                placeholder="Tell us about your goals and what you're looking for..."
              />
            </div>
            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? "Sending..." : "Send Message"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
