-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 30-05-2025 a las 18:15:04
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `serenazgo_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `intervalosreporte`
--

CREATE TABLE `intervalosreporte` (
  `ID_Intervalo` int(11) NOT NULL,
  `ID_Turno` int(11) NOT NULL,
  `Hora_Inicio_Reporte` time NOT NULL,
  `Hora_Fin_Reporte` time NOT NULL,
  `Frecuencia_Minutos` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ocurrencias`
--

CREATE TABLE `ocurrencias` (
  `ID_Ocurrencia` int(11) NOT NULL,
  `Fecha_Hora_Ocurrencia` datetime NOT NULL,
  `Descripcion` text NOT NULL,
  `Ubicacion` varchar(255) DEFAULT NULL,
  `Fecha_Creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

CREATE TABLE `roles` (
  `id` int(11) NOT NULL,
  `nombre_rol` varchar(50) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `serenazgos`
--

CREATE TABLE `serenazgos` (
  `id` int(11) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellido_paterno` varchar(100) NOT NULL,
  `apellido_materno` varchar(100) NOT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `foto` varchar(255) DEFAULT NULL,
  `celular` varchar(15) DEFAULT NULL,
  `dni` varchar(8) NOT NULL,
  `estado_empleo` enum('activo','inactivo','licencia','suspendido') DEFAULT 'activo',
  `cargo` varchar(100) DEFAULT NULL,
  `fecha_ingreso` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tbl_kmappo`
--

CREATE TABLE `tbl_kmappo` (
  `IDKM` int(11) NOT NULL,
  `ID_Unidad` int(11) NOT NULL,
  `KM` int(11) DEFAULT NULL,
  `AP` int(11) DEFAULT NULL,
  `PO` int(11) DEFAULT NULL,
  `ID_Turno` int(11) NOT NULL,
  `obs_turno` varchar(255) DEFAULT NULL,
  `hora_Registro` time DEFAULT NULL,
  `fecha_Registro` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tbl_kmappo`
--

INSERT INTO `tbl_kmappo` (`IDKM`, `ID_Unidad`, `KM`, `AP`, `PO`, `ID_Turno`, `obs_turno`, `hora_Registro`, `fecha_Registro`) VALUES
(36, 9, 90, 230, 3, 2, 'NOCHE-DÍA', '09:18:15', '2025-05-30'),
(37, 10, 45, 220, 2, 2, 'DÍA', '09:18:15', '2025-05-30'),
(38, 11, 20, 180, 4, 2, 'NOCHE-TARDE', '09:18:15', '2025-05-30'),
(39, 9, 90, 230, 2, 2, 'NOCHE-DÍA', '09:45:40', '2025-05-30');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tbl_reportuni`
--

CREATE TABLE `tbl_reportuni` (
  `ID_Reporte` int(11) NOT NULL,
  `IDKM` int(11) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `hora_Reporte` time NOT NULL,
  `fecha_Reporte` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turnos`
--

CREATE TABLE `turnos` (
  `ID_Turno` int(11) NOT NULL,
  `Nombre_Turno` varchar(50) NOT NULL,
  `Hora_Inicio` time NOT NULL,
  `Hora_Fin` time NOT NULL,
  `Descripcion` text DEFAULT NULL,
  `Fecha_Creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `turnos`
--

INSERT INTO `turnos` (`ID_Turno`, `Nombre_Turno`, `Hora_Inicio`, `Hora_Fin`, `Descripcion`, `Fecha_Creacion`) VALUES
(1, 'NOCHE', '22:00:00', '06:00:00', NULL, '2025-05-28 11:56:41'),
(2, 'DÍA', '06:00:00', '14:00:00', NULL, '2025-05-28 11:56:41'),
(3, 'TARDE', '14:00:00', '22:00:00', NULL, '2025-05-28 11:56:41');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `unidades`
--

CREATE TABLE `unidades` (
  `ID_Unidad` int(11) NOT NULL,
  `Numero_Placa` varchar(10) NOT NULL,
  `Modelo` varchar(50) DEFAULT NULL,
  `Marca` varchar(50) DEFAULT NULL,
  `Estado` enum('operativa','mantenimiento','fuera_de_servicio') DEFAULT 'operativa',
  `Fecha_Creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `unidades`
--

INSERT INTO `unidades` (`ID_Unidad`, `Numero_Placa`, `Modelo`, `Marca`, `Estado`, `Fecha_Creacion`) VALUES
(1, 'EUI-621', 'Pick-ups', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(2, 'EUI-682', 'Pick-ups', 'Korea', 'mantenimiento', '2025-05-28 11:43:49'),
(3, 'EUI-683', 'Pick-ups', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(4, 'EUI-646', 'Pick-ups', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(5, 'EUI-685', 'Pick-ups', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(6, 'EUI-686', 'Pick-ups', 'Korea', 'fuera_de_servicio', '2025-05-28 11:43:49'),
(7, 'EUI-679', 'Pick-ups', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(8, 'EUI-680', 'Pick-ups', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(9, 'EUI-645', 'Auto Sedan', 'Korea', 'operativa', '2025-05-28 11:43:49'),
(10, 'EUI-647', 'Auto Sedan', 'Korea', 'mantenimiento', '2025-05-28 11:43:49'),
(11, 'EUI-668', 'Auto Sedan', 'Korea', 'operativa', '2025-05-28 11:43:49');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `id_serenazgo` int(11) DEFAULT NULL,
  `id_rol` int(11) NOT NULL,
  `nombre_usuario` varchar(50) NOT NULL,
  `clave_encriptada` varchar(255) NOT NULL,
  `estado` enum('activo','inactivo') DEFAULT 'activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `intervalosreporte`
--
ALTER TABLE `intervalosreporte`
  ADD PRIMARY KEY (`ID_Intervalo`),
  ADD KEY `ID_Turno` (`ID_Turno`);

--
-- Indices de la tabla `ocurrencias`
--
ALTER TABLE `ocurrencias`
  ADD PRIMARY KEY (`ID_Ocurrencia`);

--
-- Indices de la tabla `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre_rol` (`nombre_rol`);

--
-- Indices de la tabla `serenazgos`
--
ALTER TABLE `serenazgos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `dni` (`dni`);

--
-- Indices de la tabla `tbl_kmappo`
--
ALTER TABLE `tbl_kmappo`
  ADD PRIMARY KEY (`IDKM`),
  ADD KEY `ID_Unidad` (`ID_Unidad`),
  ADD KEY `ID_Turno` (`ID_Turno`);

--
-- Indices de la tabla `tbl_reportuni`
--
ALTER TABLE `tbl_reportuni`
  ADD PRIMARY KEY (`ID_Reporte`),
  ADD KEY `ID_Unidad` (`IDKM`);

--
-- Indices de la tabla `turnos`
--
ALTER TABLE `turnos`
  ADD PRIMARY KEY (`ID_Turno`),
  ADD UNIQUE KEY `Nombre_Turno` (`Nombre_Turno`);

--
-- Indices de la tabla `unidades`
--
ALTER TABLE `unidades`
  ADD PRIMARY KEY (`ID_Unidad`),
  ADD UNIQUE KEY `Numero_Placa` (`Numero_Placa`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre_usuario` (`nombre_usuario`),
  ADD UNIQUE KEY `id_serenazgo` (`id_serenazgo`),
  ADD KEY `id_rol` (`id_rol`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `intervalosreporte`
--
ALTER TABLE `intervalosreporte`
  MODIFY `ID_Intervalo` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ocurrencias`
--
ALTER TABLE `ocurrencias`
  MODIFY `ID_Ocurrencia` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `serenazgos`
--
ALTER TABLE `serenazgos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `tbl_kmappo`
--
ALTER TABLE `tbl_kmappo`
  MODIFY `IDKM` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT de la tabla `tbl_reportuni`
--
ALTER TABLE `tbl_reportuni`
  MODIFY `ID_Reporte` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `turnos`
--
ALTER TABLE `turnos`
  MODIFY `ID_Turno` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `unidades`
--
ALTER TABLE `unidades`
  MODIFY `ID_Unidad` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `intervalosreporte`
--
ALTER TABLE `intervalosreporte`
  ADD CONSTRAINT `intervalosreporte_ibfk_1` FOREIGN KEY (`ID_Turno`) REFERENCES `turnos` (`ID_Turno`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `tbl_kmappo`
--
ALTER TABLE `tbl_kmappo`
  ADD CONSTRAINT `tbl_kmappo_ibfk_1` FOREIGN KEY (`ID_Unidad`) REFERENCES `unidades` (`ID_Unidad`);

--
-- Filtros para la tabla `tbl_reportuni`
--
ALTER TABLE `tbl_reportuni`
  ADD CONSTRAINT `tbl_reportuni_ibfk_1` FOREIGN KEY (`IDKM`) REFERENCES `unidades` (`ID_Unidad`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `tbl_reportuni_ibfk_2` FOREIGN KEY (`rno`) REFERENCES `turnos` (`ID_Turno`) ON UPDATE CASCADE;

--
-- Filtros para la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `usuarios_ibfk_2` FOREIGN KEY (`id_serenazgo`) REFERENCES `serenazgos` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
