## ADDED Requirements

### Requirement: Landing page hero section
The landing page SHALL display a full-screen hero section with animated background, school name "David House - Camino de Vida", tagline, CTA buttons ("Conócenos", "Aula Virtual"), and decorative floating shapes.

#### Scenario: Hero renders correctly
- **WHEN** any user visits the root URL `/`
- **THEN** the hero section SHALL be visible with the school name, tagline, and both CTA buttons

### Requirement: Stats bar
The landing page SHALL display a stats bar below the hero with 4 stat items: "Años de Experiencia", "Estudiantes", "Niveles Educativos", "Satisfacción" with icons and animated counters.

#### Scenario: Stats bar visible on scroll
- **WHEN** user scrolls past the hero section
- **THEN** the stats bar SHALL be visible with all 4 stat items

### Requirement: About section
The landing page SHALL have a "Nosotros" section with placeholder image and descriptive text about the institution.

#### Scenario: Nosotros section visible
- **WHEN** user clicks "Conócenos" or scrolls to #nosotros
- **THEN** the section SHALL display with image placeholder and institution description

### Requirement: Values section
The landing page SHALL display 4 value cards: "Amor y Respeto", "Trabajo en Equipo", "Excelencia Académica", "Innovación Educativa" with icons and descriptions.

#### Scenario: Values displayed
- **WHEN** user scrolls to the values section
- **THEN** 4 value cards SHALL be visible in a responsive grid

### Requirement: Mission and Vision section
The landing page SHALL display Mission and Vision cards side by side with icons and descriptive text.

#### Scenario: Mission/Vision displayed
- **WHEN** user scrolls to #mision-vision
- **THEN** both Mission and Vision cards SHALL be displayed

### Requirement: Educational levels section
The landing page SHALL show "Inicial" (3-5 years) and "Primaria" (6-11 years) level cards with feature lists.

#### Scenario: Levels section displayed
- **WHEN** user scrolls to #niveles
- **THEN** both Inicial and Primaria cards SHALL be visible with their features

### Requirement: Gallery section
The landing page SHALL display a responsive image gallery grid (6 placeholder items).

#### Scenario: Gallery rendered
- **WHEN** user scrolls to #galeria
- **THEN** a 3-column grid of 6 gallery items SHALL be displayed

### Requirement: Footer
The landing page SHALL have a footer with brand info, quick links, contact details, social media links, and "Aula Virtual" access button.

#### Scenario: Footer visible
- **WHEN** user scrolls to the bottom of the page
- **THEN** the footer SHALL display with all sections

### Requirement: Event carousel (auto-scroll)
The landing page SHALL include an event carousel section that auto-scrolls left-to-right showing event image, title, and brief description. Events SHALL be stored in a new `eventos` table. The carousel SHALL use CSS animation for smooth infinite scroll.

#### Scenario: Carousel auto-scrolls
- **WHEN** the landing page loads and events exist in the database
- **THEN** the carousel SHALL automatically scroll events from left to right in a continuous loop

#### Scenario: Carousel shows event details
- **WHEN** an event is displayed in the carousel
- **THEN** the event image, title, and description SHALL be visible

#### Scenario: Empty carousel state
- **WHEN** no events exist in the database
- **THEN** the carousel section SHALL display a "No hay eventos próximos" message

### Requirement: Scroll reveal animations
Sections on the landing page SHALL fade in and slide up as the user scrolls.

#### Scenario: Sections animate on scroll
- **WHEN** user scrolls to a new section
- **THEN** the section SHALL animate in with a fade+slide-up transition
